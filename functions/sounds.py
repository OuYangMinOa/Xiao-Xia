from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.info       import logger
from utils.info       import sound_user, music_user, recording
from glob             import glob
from utils.upload     import upload_wp
from utils.music_ui   import SoundboardView, info_embed, error_embed, COLOR_DONE

import utils.MusicBot     as my_mb # my class
import utils.loudness     as loudness
import discord
import asyncio
import os


SOUND_EXTENSIONS = ('.mp3', '.wav')


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


def sound_folder(guild_id):
    return os.path.join("data/attachments", str(guild_id))

def list_sounds(guild_id, keyword=None):
    """(labels, files) of the guild's sounds, oldest upload first."""
    files = [path for path in glob(f'{sound_folder(guild_id)}/*.*')
             if path.lower().endswith(SOUND_EXTENSIONS) and os.path.basename(path) != 'empty.wav']
    files.sort(key=os.path.getmtime)
    labels = [os.path.splitext(os.path.basename(path))[0] for path in files]
    files  = [os.path.basename(path) for path in files]
    if (keyword):
        keyword = keyword.lower()
        pairs   = [(l, f) for l, f in zip(labels, files) if keyword in l.lower()]
        labels  = [l for l, _ in pairs]
        files   = [f for _, f in pairs]
    return labels, files


def music_bot_in_guild(guild_id):
    for each in music_user.values():
        if (each.ctx.guild.id == guild_id):
            return each
    return None


async def ensure_sound_bot(bot, source, member):
    """The SoundBot for source's text channel, joining member's voice channel if needed.

    Args:
        source: an ApplicationContext or an Interaction (only .channel and .guild are used)
        member: who asked; the bot follows them into their voice channel

    Returns:
        (SoundBot | None, str | None): the bot, or None and the reason
    """
    if (not member.voice or not member.voice.channel):
        return None, "你要先加入語音頻道"
    channel = member.voice.channel
    key     = source.channel.id
    voice   = source.guild.voice_client

    if (voice is not None and not voice.is_connected()):
        voice = None

    sound_bot = sound_user.get(key)
    if (sound_bot is not None and sound_bot.live and voice is not None and sound_bot.voice is voice):
        if (voice.channel.id != channel.id):
            await voice.move_to(channel)
            logger.info(f"[*] move {sound_bot.channelid} -> {channel.id}")
        sound_bot.channel, sound_bot.channelid = channel, channel.id
        return sound_bot, None

    if (sound_bot is not None):
        await sound_bot.kill()
        del sound_user[key]

    if (voice is None):
        logger.info("[*] moving to voice channel")
        voice = await channel.connect(timeout = 60)
    elif (voice.channel.id != channel.id):
        await voice.move_to(channel)

    # the music player of this guild shares the voice client
    music_bot = music_bot_in_guild(source.guild.id)
    if (music_bot is not None):
        music_bot.voice, music_bot.channel, music_bot.channelid = voice, channel, channel.id

    sound_bot = SoundBot(channel, voice, source, bot)
    sound_user[key] = sound_bot
    return sound_bot, None


class Sounds(discord.ext.commands.Cog):
    responds_itself = True   # skip the global defer in main.py's before_invoke

    def __init__(self, bot):
        self.bot = bot

    def _board(self, guild_id, labels, files, title, timeout=6 * 60 * 60):
        async def play(interaction, file):
            try:
                sound_bot, error = await ensure_sound_bot(self.bot, interaction, interaction.user)
            except Exception as e:
                logger.error(f"[*] soundboard could not join the voice channel : {e}")
                return "連不上語音頻道，等一下再試試"
            if (error):
                return error
            if (not os.path.isfile(os.path.join(sound_folder(guild_id), file))):
                return "這個音效已經不存在了，重新開一次 `/list_sound` 吧"
            logger.info(f"[*] sound {file} - {interaction.user.name}")
            asyncio.create_task(sound_bot.playSound(file))
            return None

        async def stop(interaction):
            sound_bot = sound_user.get(interaction.channel.id)
            if (sound_bot is None or sound_bot.state == 0):
                return "現在沒有在播音效"
            await sound_bot.skip()
            return None

        return SoundboardView(labels, files, play, stop, title=title, timeout=timeout)

    @slash_command( name="upload_sound",description="upload sound file")
    async def upload_sound(self,ctx : discord.ApplicationContext, filename : Option(str, "The name of the sound", required = True), file: discord.Attachment):
        logger.info(f"upload_sound {ctx.author.name}")

        attachment_name = (file.filename or "").lower()
        if (not attachment_name.endswith(SOUND_EXTENSIONS)):
            await ctx.respond(embed=error_embed("只接受 mp3 或 wav 檔"), ephemeral=True)
            return
        await ctx.defer(ephemeral=True)

        # the name ends up in a path; keep it from escaping the guild's folder
        name        = my_mb.safe_song_filename(filename, fallback="sound")
        file_extend = "mp3" if attachment_name.endswith('mp3') else "wav"
        save_folder = sound_folder(ctx.guild.id)
        os.makedirs(save_folder,exist_ok=True)
        save_path   = f"{save_folder}/{name}.{file_extend}"
        replaced    = os.path.isfile(save_path)
        await file.save(save_path)
        logger.info(f"[*] {name}.{file_extend} received."+ f' - {ctx.guild.id}:{ctx.author.name}')

        # measure the loudness now so the first play is already normalized
        # (the gain itself is applied at playback, see utils/loudness.py)
        await loudness.get_filter(save_path, timeout=None)
        if (str(ctx.guild.id) == os.getenv('MYDISCORDGID')):
            await upload_wp(save_path)

        verb = "更新" if replaced else "新增"
        await ctx.respond(embed=info_embed(f"✅ 已{verb}音效 **{discord.utils.escape_markdown(name)}**，用 `/list_sound` 就能播放", COLOR_DONE))

    @slash_command(name="list_sound",description="list all the sounds in this channel")
    async def list_sound(self,ctx : discord.ApplicationContext):
        logger.info(f"[*] list sound"+ f' - {ctx.author.name}')
        labels, files = list_sounds(ctx.guild.id)
        if (len(labels) == 0):
            await ctx.respond(embed=error_embed("這個伺服器還沒有音效，用 `/upload_sound` 上傳一個吧"), ephemeral=True)
            return

        await ctx.defer()
        try:
            _, error = await ensure_sound_bot(self.bot, ctx, ctx.author)
        except Exception as e:
            logger.error(e)
            error = "連不上語音頻道，等一下再試試"
        if (error):
            await ctx.respond(embed=error_embed(error))
            return

        board = self._board(ctx.guild.id, labels, files, "🔊 音效板")
        await ctx.respond(embed=board.embed(), view=board)

    @slash_command( name="search_sound",description="Search sound file")
    async def search_sound(self,ctx : discord.ApplicationContext, keyword:Option(str, "The keywords", required = True)):
        logger.info(f"[*] search sound"+ f'{keyword}  - {ctx.author.name}')
        labels, files = list_sounds(ctx.guild.id, keyword)
        if (len(labels) == 0):
            await ctx.respond(embed=error_embed(f"找不到含有「{discord.utils.escape_markdown(keyword)}」的音效"), ephemeral=True)
            return

        await ctx.defer(ephemeral=True)
        try:
            _, error = await ensure_sound_bot(self.bot, ctx, ctx.author)
        except Exception as e:
            logger.error(e)
            error = "連不上語音頻道，等一下再試試"
        if (error):
            await ctx.respond(embed=error_embed(error))
            return

        # ephemeral messages can only be edited for 15 minutes
        board = self._board(ctx.guild.id, labels, files, f"🔍 音效搜尋：{keyword}", timeout=14 * 60)
        await ctx.respond(embed=board.embed(), view=board)


class SoundBot(my_mb.MusicBot):
    SHOW_PANEL = False

    def __init__(self,channel, voice , ctx, client):
        super().__init__(channel, voice , ctx, client)
        self.floder = f"data/attachments/{ctx.guild.id}"
        self.loop   = False
        self._sound_turn   = 0      # bumped by every playSound, so only the latest one resumes the music
        self._paused_music = None   # (MusicBot, position) interrupted by sounds

    async def playSound(self,thisFile):
        self._sound_turn += 1
        turn = self._sound_turn

        ## pause the music of this guild while the sound plays
        music_bot = music_bot_in_guild(self.ctx.guild.id)
        if (music_bot is not None and music_bot is not self and music_bot.state == 1):
            self._paused_music = (music_bot, music_bot.startTime)
            await music_bot.pause("🔊 播放音效中，音樂稍等一下")
            music_bot.state = 3

        await self.clear()
        self.queqed = [(thisFile,''), ]
        logger.info(self.queqed)

        ## Start the sound
        await self._next()

        ## if the sound finished playing
        while self.StartCount:
            await asyncio.sleep(0.3)

        if (turn != self._sound_turn or self._paused_music is None):
            return   # another sound took over; it resumes the music when it ends

        ## resume the music
        music_bot, position = self._paused_music
        self._paused_music  = None
        if (music_bot.live and music_bot.state == 3):
            music_bot.startTime = position
            music_bot.note("")
            await music_bot.pause()

    async def leave(self):
        record_user_guild = [recording[x ].ctx.guild.id for x in recording]
        if (self.ctx.guild.id in record_user_guild):
            record_channel_id = recording[list(recording)[record_user_guild.index(self.ctx.guild.id)]].ctx.channel.id
            await recording[record_channel_id].kill()

        await super().leave()


def setup(bot : discord.Bot):
    bot.add_cog(Sounds(bot))
