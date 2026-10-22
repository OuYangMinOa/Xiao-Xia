from discord.commands import slash_command, Option
from discord.ext      import commands

from utils.info       import logger, CheckBool
from utils.info       import music_user, sound_user, Playlist_folder, MUSIC_folder, recording

from utils.PlayListSelection import PlayListSelection
from utils.music_ui   import info_embed, error_embed, added_embed, shorten, COLOR_DONE
from utils.playlist_editor import (PlaylistEditor, LiveQueueSource, SavedPlaylistSource, list_playlists,
                                   playlist_path, write_playlist, clean_playlist_name)

import utils.MusicBot     as my_mb # my class
import threading
import edge_tts
import discord
import asyncio
import os


async def playlist_names(ctx : discord.AutocompleteContext):
    typed = (ctx.value or "").lower()
    return [name for name in list_playlists(ctx.interaction.guild.id) if typed in name.lower()][:25]


class Music(discord.ext.commands.Cog):
    responds_itself = True   # skip the global defer in main.py's before_invoke

    def __init__(self, bot):
        self.bot = bot

    # ------------------------------------------------------------ helpers

    async def _reply(self, ctx, text, ephemeral=True, error=False):
        embed = error_embed(text) if error else info_embed(text)
        await ctx.respond(embed=embed, ephemeral=ephemeral)

    async def _require_voice(self, ctx):
        """The author's voice channel, or None after telling them to join one."""
        if (not ctx.author.voice or not ctx.author.voice.channel):
            await self._reply(ctx, "你要先加入語音頻道", error=True)
            return None
        return ctx.author.voice.channel

    async def _active_music(self, ctx):
        """The MusicBot playing for this channel, or None after saying so."""
        if (await self._require_voice(ctx) is None):
            return None
        mb = music_user.get(ctx.channel.id)
        if (mb is None or ctx.guild.voice_client not in self.bot.voice_clients):
            await self._reply(ctx, "我現在沒有在放歌，用 `/play` 點一首吧", error=True)
            return None
        return mb

    def _sound_bot_in_guild(self, guild_id):
        for each in sound_user.values():
            if (each.ctx.guild.id == guild_id):
                return each
        return None

    async def _music_bot(self, ctx, channel):
        """The MusicBot for this text channel, joining / moving to `channel` as needed."""
        mb = music_user.get(ctx.channel.id)
        if (mb is not None):
            if ctx.guild.voice_client not in self.bot.voice_clients:   # in same channel but not in any voice channel
                logger.info("[*] rejoin the voice channel")
                await mb.kill()
                del music_user[ctx.channel.id]
            else:
                if (mb.channelid != channel.id):  # in same channel but not in same voice channel
                    await mb.voice.move_to(channel)
                    logger.info(f"[*] move {mb.channelid} -> {channel.id}")
                    mb.channel    = channel
                    mb.channelid  = channel.id
                mb.ctx = ctx
                return mb

        sound_bot = self._sound_bot_in_guild(ctx.guild.id)
        if (sound_bot is not None and sound_bot.voice.is_connected()):
            # take over the voice client of the soundboard
            voice = sound_bot.voice
            await sound_bot.clear()
            if (voice.channel.id != channel.id):
                await voice.move_to(channel)
        elif (ctx.guild.voice_client is not None and ctx.guild.voice_client.is_connected()):
            voice = ctx.guild.voice_client
            if (voice.channel.id != channel.id):
                await voice.move_to(channel)
        else:
            voice = await channel.connect(timeout = 60)

        mb = my_mb.MusicBot(channel, voice , ctx, self.bot)
        logger.info(f"[*] creating Class id : {id(mb)} for serving channel {channel.id}")
        music_user[ctx.channel.id] = mb
        return mb

    async def _queue(self, ctx, url, next=False):
        channel = await self._require_voice(ctx)
        if (channel is None):
            return
        await ctx.defer()
        try:
            mb = await self._music_bot(ctx, channel)
        except Exception as e:
            logger.error(f"[*] Error connecting to voice channel: {e}")
            await ctx.respond(embed=error_embed("連不上語音頻道，等一下再試試"))
            return

        result = await mb.add(url, next=next, requester=ctx.author.mention)
        if (not result["ok"]):
            await ctx.respond(embed=error_embed(result["error"]))
        else:
            await ctx.respond(embed=added_embed(result, ctx.author))

    # ------------------------------------------------------------ playback

    @slash_command(name="play",description="play the music (supporting spotify and youtube)")
    async def play(self,ctx : discord.ApplicationContext,  url: Option(str, "YouTube / Spotify url, or a song name to search", required = False)):
        logger.info(f'[*] {url} - {ctx.author.name}')
        if (url):
            await self._queue(ctx, url)
            return

        # no url : resume whatever was paused
        mb = await self._active_music(ctx)
        if (mb is None):
            return
        sound_bot = self._sound_bot_in_guild(ctx.guild.id)
        if (sound_bot is not None):
            await sound_bot.clear()
        if (mb.state in (2, 3)):
            mb.note(f"▶️ {ctx.author.display_name} 繼續播放")
            await self._reply(ctx, "▶️ 繼續播放")
            await mb.pause()
        elif (mb.state == 0 and len(mb.queqed) > 0):
            await self._reply(ctx, "▶️ 開始播放")
            await mb.skip()
        else:
            await self._reply(ctx, "用 `/play 連結或歌名` 來點歌")

    @slash_command(name="play_next",description="Insert a music to the next of the playlist")
    async def play_next(self,ctx : discord.ApplicationContext,  url: Option(str, "YouTube / Spotify url, or a song name to search", required = True)):
        logger.info(f'[*] {url} - {ctx.author.name}')
        await self._queue(ctx, url, next=True)

    @slash_command(name="pause",description="Pause / resume the music")
    async def pause(self,ctx : discord.ApplicationContext):
        mb = await self._active_music(ctx)
        if (mb is None):
            return
        if (mb.state == 1):
            text = f"⏸️ {ctx.author.display_name} 暫停了播放"
        else:
            text = f"▶️ {ctx.author.display_name} 繼續播放"
        mb.note(text)
        await self._reply(ctx, text)
        await mb.toggle_pause()

    @slash_command(name="skip",description="skip the current music")
    async def skip(self,ctx : discord.ApplicationContext):
        if (ctx.channel.id in sound_user and ctx.channel.id not in music_user):
            if (await self._require_voice(ctx) is None):
                return
            await self._reply(ctx, "⏹️ 已停止音效")
            await sound_user[ctx.channel.id].skip()
            return
        await self._skip_music(ctx)

    @slash_command(name="stop_music",description="skip the current music")
    async def stop_music(self,ctx : discord.ApplicationContext):
        await self._skip_music(ctx)

    async def _skip_music(self, ctx):
        mb = await self._active_music(ctx)
        if (mb is None):
            return
        title = shorten(mb.this_song[0], 60) if mb.this_song else ""
        mb.note(f"⏭️ {ctx.author.display_name} 跳過了 {title}")
        await self._reply(ctx, f"⏭️ 跳過了 **{title}**")
        await mb.skip()

    @slash_command(name="stop_sound",description="skip the current sound")
    async def stop_sound(self,ctx : discord.ApplicationContext):
        if (await self._require_voice(ctx) is None):
            return
        if (ctx.channel.id not in sound_user):
            await self._reply(ctx, "現在沒有在播音效", error=True)
            return
        await self._reply(ctx, "⏹️ 已停止音效")
        await sound_user[ctx.channel.id].skip()

    @slash_command(name="skipnums",description="skip several songs at once")
    async def skipnums(self,ctx : discord.ApplicationContext,  nums: Option(int, "The number of music you want to skip", required = True, min_value = 1)):
        logger.info(f'[*] {nums} - {ctx.author.name}')
        mb = await self._active_music(ctx)
        if (mb is None):
            return
        mb.note(f"⏭️ {ctx.author.display_name} 一次跳過了 {nums} 首")
        await self._reply(ctx, f"⏭️ 跳過 {nums} 首")
        await mb.skipnums(nums)

    @slash_command(name="loop",description="loop the music list")
    async def loop(self,ctx : discord.ApplicationContext):
        mb = await self._active_music(ctx)
        if (mb is None):
            return
        enabled = not mb.loop
        await self._reply(ctx, "🔁 開啟循環播放" if enabled else "➡️ 關閉循環播放")
        await mb.set_loop(enabled, ctx.author.display_name)

    @slash_command(name="shuffle",description="shuffle the songs in the queue")
    async def shuffle(self,ctx : discord.ApplicationContext):
        mb = await self._active_music(ctx)
        if (mb is None):
            return
        if (len(mb.queqed) < 2):
            await self._reply(ctx, "接下來的歌不到兩首，沒什麼好打亂的", error=True)
            return
        mb.note(f"🔀 {ctx.author.display_name} 打亂了播放順序")
        await self._reply(ctx, "🔀 已打亂播放順序")
        await mb.shuffle()

    @slash_command(name="list",description="List all the music")
    async def list(self,ctx : discord.ApplicationContext):
        mb = await self._active_music(ctx)
        if (mb is None):
            return
        logger.info(f"[*] {mb.channelid} is asking the playlist")
        editor = PlaylistEditor(LiveQueueSource(mb))
        await ctx.respond(embed=editor.render(), view=editor, ephemeral=True)

    @slash_command(name="nowplaying",description="Bring the player panel back to the bottom of the chat")
    async def nowplaying(self,ctx : discord.ApplicationContext):
        mb = await self._active_music(ctx)
        if (mb is None):
            return
        if (mb.ui_status == "idle"):
            await self._reply(ctx, "現在沒有在播放，用 `/play` 點一首吧", error=True)
            return
        await self._reply(ctx, "👇 播放面板在這")
        await mb.update_panel(move=True)

    @slash_command(name="clear",description="clear the music")
    async def clear(self,ctx : discord.ApplicationContext):
        mb = await self._active_music(ctx)
        if (mb is None):
            return
        logger.info(f"[*] Music : {mb.channelid} cleared")
        mb.note(f"🧹 {ctx.author.display_name} 清空了佇列")
        await self._reply(ctx, "🧹 已清空佇列")
        await mb.clear()

    @slash_command(name="leave",description="leave the voice channel")
    async def leave(self,ctx : discord.ApplicationContext):
        if (await self._require_voice(ctx) is None):
            return
        if ctx.guild.voice_client not in self.bot.voice_clients:
            await self._reply(ctx, "我已經不在語音頻道了", error=True)
            return
        await self._reply(ctx, f"👋 {ctx.author.display_name} 讓我離開了語音頻道", ephemeral=False)

        if (ctx.channel.id in music_user):
            await music_user[ctx.channel.id].leave()

        if (ctx.channel.id in sound_user):
            for eachctx in list(sound_user[ctx.channel.id].ctxResArr):
                try:
                    if (isinstance(eachctx,discord.WebhookMessage) or isinstance(eachctx,discord.Message)):
                        await eachctx.delete()
                    else:
                        await eachctx.delete_original_response()
                    sound_user[ctx.channel.id].ctxResArr.remove(eachctx)
                except Exception as e:
                    logger.error(f"[*] Delete original response : {e}")
            await sound_user[ctx.channel.id].leave()

        if (ctx.guild.voice_client is not None):
            await ctx.guild.voice_client.disconnect()

    # ------------------------------------------------------------ saved playlists

    @slash_command(name='save_playlist',description="Save current playlist")
    async def savePlaylist(self,ctx : discord.ApplicationContext, name : Option(str, "The name of the playlist", required = True)):
        logger.info(f'[*] playlist : {name} - {ctx.author.name} in guild id - {ctx.guild.id}')

        this_misuser = next((each for each in music_user.values() if each.ctx.guild.id == ctx.guild.id), None)
        if (this_misuser is None):
            await self._reply(ctx, "我現在沒有在放歌，沒有清單可以存", error=True)
            return

        thisPlaylist = this_misuser.passed + this_misuser.queqed
        if (len(thisPlaylist)==0):
            await self._reply(ctx, "播放清單是空的", error=True)
            return

        name = clean_playlist_name(name)
        Playlist_filename = playlist_path(ctx.guild.id, name)
        write_playlist(Playlist_filename, thisPlaylist)

        await ctx.respond(embed=info_embed(f"💾 已儲存歌單 **{discord.utils.escape_markdown(name)}**（{len(thisPlaylist)} 首），"
                                           f"用 `/playlist` 播放、`/edit_playlist` 編輯", COLOR_DONE))
        logger.info(f"[*] playlist save in {Playlist_filename}")

    @slash_command(name="playlist",description="list all the playlist")
    async def playlist(self,ctx : discord.ApplicationContext):
        logger.info(f'[*] load_playlist - {ctx.guild.id}')
        channel = await self._require_voice(ctx)
        if (channel is None):
            return

        guildPlaylistFolder = os.path.join(Playlist_folder,f"{ctx.guild.id}")
        PLS = PlayListSelection(None, guildPlaylistFolder)
        if (len(PLS.label) == 0):
            await self._reply(ctx, "還沒有存過歌單，用 `/save_playlist` 存一個吧", error=True)
            return

        await ctx.defer()
        try:
            PLS.music_class = await self._music_bot(ctx, channel)
        except Exception as e:
            logger.error(f"[*] Error connecting to voice channel: {e}")
            await ctx.respond(embed=error_embed("連不上語音頻道，等一下再試試"))
            return
        await ctx.respond(embed=info_embed(f"📂 共有 {len(PLS.label)} 個歌單，選一個開始播放（要改內容用 `/edit_playlist`）"), view=PLS.view)

    @slash_command(name="edit_playlist",description="Edit a saved playlist: reorder, remove or add songs, rename or delete it")
    async def edit_playlist(self,ctx : discord.ApplicationContext, name : Option(str, "The name of the playlist", required = True, autocomplete = playlist_names)):
        logger.info(f'[*] edit_playlist : {name} - {ctx.author.name} in guild id - {ctx.guild.id}')
        if (name not in list_playlists(ctx.guild.id)):
            await self._reply(ctx, f"找不到叫 {discord.utils.escape_markdown(name)} 的歌單", error=True)
            return
        editor = PlaylistEditor(SavedPlaylistSource(ctx.guild.id, name), play_saved=self._play_saved)
        await ctx.respond(embed=editor.render(), view=editor, ephemeral=True)

    async def _play_saved(self, interaction, name, songs):
        """The "play this playlist" button of the editor. Returns an error or None."""
        if (not songs):
            return "歌單是空的"
        voice = getattr(interaction.user, "voice", None)
        if (voice is None or voice.channel is None):
            return "你要先加入語音頻道"
        try:
            mb = await self._music_bot(interaction, voice.channel)
        except Exception as e:
            logger.error(f"[*] Error connecting to voice channel: {e}")
            return "連不上語音頻道，等一下再試試"
        await mb.clear()
        mb.queqed = [tuple(each) for each in songs]
        mb.passed = []
        mb.note(f"📂 {interaction.user.display_name} 播放了歌單 {name}")
        await interaction.channel.send(embed=info_embed(
            f"📂 {interaction.user.mention} 開始播放歌單 **{discord.utils.escape_markdown(name)}**（{len(songs)} 首）", COLOR_DONE))
        mb.state = 1
        asyncio.create_task(mb._safe_next())
        return None

    # ------------------------------------------------------------ tts

    @slash_command(name="say",description="Let me say something")
    async def say(self,ctx : discord.ApplicationContext, word:Option(str,"THe word you want me to say",required=True)):
        logger.info(f'[*] {ctx.author.name} - {word}')
        channel = await self._require_voice(ctx)
        if (channel is None):
            return
        await ctx.respond(embed=info_embed(f"🗣️ {discord.utils.escape_markdown(word)}"), ephemeral=True)

        try:
            mb = await self._music_bot(ctx, channel)
        except Exception as e:
            logger.error(e)
            return

        logger.info(f"[*] creating sound .... ")
        os.makedirs(MUSIC_folder,exist_ok=True)
        filename = f"{MUSIC_folder}//{ctx.guild.id}.mp3"

        ## say something
        VOICE = "zh-CN-YunxiNeural"
        communicate = edge_tts.Communicate(word, VOICE,rate= "-5%",volume="+50%")
        await communicate.save(filename)

        logger.info(f"[*] Build sound successful !!")


        lastMusicTime = mb.startTime
        stateBefore   = mb.state
        if (stateBefore == 1):
            await mb.pause(f"🗣️ {ctx.author.display_name} 讓我說話，音樂先暫停")

        tempqueqe = mb.queqed
        temppasse = mb.passed
        tempsong  = mb.this_song

        mb.passed = []
        mb.queqed = [ (f"{ctx.guild.id}.mp3",""),]
        logger.info(f"[*] Try to play sound .... ")


        await mb._next()

        while mb.StartCount:
            await asyncio.sleep(0.5)

        mb.queqed    = tempqueqe
        mb.passed    = temppasse
        mb.this_song = tempsong
        if (stateBefore in (1, 2, 3)):
            # state 3 = replay the interrupted song from where it stopped on resume
            mb.startTime = lastMusicTime
            mb.state = 3
            if (stateBefore == 1):
                await mb.pause()
        else:
            mb.state = 0


def setup(bot : discord.Bot):
    bot.add_cog(Music(bot))
