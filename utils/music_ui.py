"""Discord UI for the music player and the soundboard: embeds and button views.

The player is one "now playing" panel per MusicBot. It is edited in place while
it is the latest message in the channel, and re-posted at the bottom when a new
song starts after other messages pushed it up. The progress bar is refreshed by
MusicBot every PROGRESS_REFRESH seconds while a song plays.
"""
import html
import math
import random
import re

import discord

from utils.info import logger


COLOR_PLAYING = 0x5865F2
COLOR_PAUSED  = 0xF0B232
COLOR_LOADING = 0x80848E
COLOR_DONE    = 0x23A55A
COLOR_ERROR   = 0xF23F43

PROGRESS_REFRESH = 15     # seconds between progress bar edits
UP_NEXT_PREVIEW  = 3      # songs listed under "接下來" on the panel
SOUNDS_PER_ROW   = 5
SOUND_ROWS       = 4      # the 5th (last) row of a view holds the board controls
SOUNDS_PER_PAGE  = SOUNDS_PER_ROW * SOUND_ROWS

_STATUS = {
    #  ui_status   : (color, header)
    "downloading": (COLOR_LOADING, "⏳ 準備中"),
    "playing"    : (COLOR_PLAYING, "🎶 正在播放"),
    "paused"     : (COLOR_PAUSED , "⏸️ 已暫停"),
}

_YT_ID = re.compile(r'(?:[?&]v=|youtu\.be/|/shorts/|/embed/|/live/)([\w-]{11})')


def youtube_id(url):
    match = _YT_ID.search(str(url or ''))
    return match.group(1) if match else None

def thumbnail_url(url):
    video_id = youtube_id(url)
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" if video_id else None

def is_web_url(url):
    return str(url or '').startswith(('http://', 'https://'))

def fmt_time(seconds):
    seconds = max(0, int(seconds or 0))
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"

def progress_bar(position, duration, width=14):
    ratio  = max(0.0, min(1.0, position / duration)) if duration else 0.0
    filled = round(ratio * width)
    return "▰" * filled + "▱" * (width - filled)

def shorten(text, limit):
    # the YouTube Data API hands back HTML escaped titles (&amp; , &#39; ...)
    text = ' '.join(html.unescape(str(text or '')).split())
    return text if len(text) <= limit else text[:limit - 1] + "…"

def song_link(title, url, limit=60):
    """Markdown link to a song, or just its name when there is no web url."""
    name = discord.utils.escape_markdown(shorten(title, limit))
    name = name.replace('[', '［').replace(']', '］')
    return f"[{name}]({url})" if is_web_url(url) else name

def member_name(member):
    return getattr(member, "display_name", None) or str(member)

def info_embed(text, color=COLOR_PLAYING):
    return discord.Embed(description=text, color=color)

def error_embed(text):
    return info_embed(f"⚠️ {text}", COLOR_ERROR)


# ------------------------------------------------------------------ embeds

def player_embed(mb):
    """The now playing panel of a MusicBot."""
    song = getattr(mb, "this_song", None)
    if (mb.ui_status not in _STATUS or not song):
        embed = discord.Embed(
            title       = "🎵 播放完畢",
            description = "佇列裡沒有歌了，用 `/play` 再點幾首吧！",
            color       = COLOR_DONE,
        )
        if (mb.last_action):
            embed.set_footer(text=mb.last_action)
        return embed

    title, url    = song[0], song[1]
    color, header = _STATUS[mb.ui_status]
    embed = discord.Embed(
        title = shorten(title, 250),
        url   = url if is_web_url(url) else None,
        color = color,
    )
    embed.set_author(name=header)

    if (mb.ui_status == "downloading"):
        embed.description = "下載音訊中，馬上就好…"
    elif (mb.is_stream):
        embed.description = "🔴 直播中"
    else:
        position = mb.position()
        if (mb.duration):
            embed.description = (f"`{fmt_time(position)}` {progress_bar(position, mb.duration)}"
                                 f" `{fmt_time(mb.duration)}`")
        else:
            embed.description = f"`{fmt_time(position)}`"

    requester = mb.requesters.get(url)
    if (requester):
        embed.add_field(name="點播", value=requester, inline=True)
    embed.add_field(name="順序", value=f"{len(mb.passed)} / {len(mb.passed) + len(mb.queqed)}", inline=True)
    embed.add_field(name="循環", value="🔁 開" if mb.loop else "關", inline=True)

    upcoming = list(mb.queqed[:UP_NEXT_PREVIEW])
    if (upcoming):
        lines = [f"`{i}.` {song_link(each[0], each[1], 50)}" for i, each in enumerate(upcoming, 1)]
        rest  = len(mb.queqed) - len(upcoming)
        if (rest > 0):
            lines.append(f"…還有 {rest} 首")
        embed.add_field(name="接下來", value="\n".join(lines), inline=False)
    elif (mb.loop):
        embed.add_field(name="接下來", value="🔁 從第一首再播一次", inline=False)

    thumbnail = thumbnail_url(url)
    if (thumbnail):
        embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text=mb.last_action or "用 /play 加歌 · 按 📜 看完整清單")
    return embed


def added_embed(result, member):
    """Reply to /play and /play_next once songs were queued."""
    if (result.get("kind") == "playlist"):
        first = result["first"]
        embed = discord.Embed(
            title       = "📃 已加入歌單",
            description = f"從 {song_link(first[0], first[1], 80)} 開始，先加入 **{result['count']}** 首"
                          + ("，其餘的在背景繼續載入" if result.get("more") else ""),
            color       = COLOR_DONE,
        )
        thumbnail = thumbnail_url(first[1])
    else:
        embed = discord.Embed(
            title       = shorten(result["title"], 250),
            url         = result["url"] if is_web_url(result["url"]) else None,
            color       = COLOR_DONE,
        )
        if (result.get("position", 0) <= 0):
            embed.description = "▶️ 馬上開始播放"
        elif (result["position"] == 1):
            embed.description = "⏭️ 下一首就播"
        else:
            embed.description = f"排在第 **{result['position']}** 首"
        thumbnail = thumbnail_url(result["url"])

    embed.set_author(name=f"{member_name(member)} 點了歌", icon_url=member.display_avatar.url)
    if (thumbnail):
        embed.set_thumbnail(url=thumbnail)
    return embed


# ------------------------------------------------------------------ views

class PlayerView(discord.ui.View):
    """Control buttons under the now playing panel."""

    def __init__(self, mb):
        super().__init__(timeout=None)
        self.mb = mb
        self.refresh()

    def refresh(self):
        mb     = self.mb
        paused = (mb.state != 1 or mb.ui_status == "paused")
        self.toggle_button.emoji = "▶️" if paused else "⏸️"
        self.toggle_button.style = discord.ButtonStyle.success if paused else discord.ButtonStyle.primary
        self.toggle_button.disabled  = mb.ui_status == "downloading"
        self.prev_button.disabled    = len(mb.passed) < 2
        self.shuffle_button.disabled = len(mb.queqed) < 2
        self.loop_button.style = discord.ButtonStyle.success if mb.loop else discord.ButtonStyle.secondary
        self.loop_button.label = "循環中" if mb.loop else "循環"

    async def interaction_check(self, interaction):
        if (not self.mb.live):
            await interaction.response.send_message(embed=error_embed("這個播放器已經關閉了，用 `/play` 重新開始"), ephemeral=True)
            return False
        voice = getattr(interaction.user, "voice", None)
        if (voice is None or voice.channel is None or voice.channel.id != self.mb.channelid):
            await interaction.response.send_message(embed=error_embed("要跟我在同一個語音頻道才能操作喔"), ephemeral=True)
            return False
        return True

    async def on_error(self, error, item, interaction):
        logger.error(f"[*] player button failed : {error}")

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def prev_button(self, button, interaction):
        await interaction.response.defer()
        self.mb.note(f"⏮️ {member_name(interaction.user)} 回到上一首")
        await self.mb.previous()

    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.primary, row=0)
    async def toggle_button(self, button, interaction):
        await interaction.response.defer()
        if (self.mb.state == 1):
            self.mb.note(f"⏸️ {member_name(interaction.user)} 暫停了播放")
        else:
            self.mb.note(f"▶️ {member_name(interaction.user)} 繼續播放")
        await self.mb.toggle_pause()

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip_button(self, button, interaction):
        await interaction.response.defer()
        title = shorten(self.mb.this_song[0], 40) if self.mb.this_song else ""
        self.mb.note(f"⏭️ {member_name(interaction.user)} 跳過了 {title}")
        await self.mb.skip()

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop_button(self, button, interaction):
        await interaction.response.defer()
        await self.mb.leave()
        await interaction.followup.send(embed=info_embed(f"👋 {member_name(interaction.user)} 讓我離開了語音頻道"))

    @discord.ui.button(emoji="🔁", label="循環", style=discord.ButtonStyle.secondary, row=1)
    async def loop_button(self, button, interaction):
        await interaction.response.defer()
        await self.mb.set_loop(not self.mb.loop, member_name(interaction.user))

    @discord.ui.button(emoji="🔀", label="隨機", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle_button(self, button, interaction):
        await interaction.response.defer()
        self.mb.note(f"🔀 {member_name(interaction.user)} 打亂了播放順序")
        await self.mb.shuffle()

    @discord.ui.button(emoji="📜", label="清單", style=discord.ButtonStyle.secondary, row=1)
    async def queue_button(self, button, interaction):
        from utils.playlist_editor import PlaylistEditor, LiveQueueSource   # imports this module
        editor = PlaylistEditor(LiveQueueSource(self.mb))
        await interaction.response.send_message(embed=editor.render(), view=editor, ephemeral=True)


class SoundboardView(discord.ui.View):
    """A page of sound buttons plus page / random / stop controls.

    play(interaction, file) and stop(interaction) are coroutines supplied by the
    sounds cog; they return an error message to show, or None on success.
    """

    def __init__(self, labels, files, play, stop, title="🔊 音效板", timeout=6 * 60 * 60):
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.sounds = list(zip(labels, files))
        self.play   = play
        self.stop_  = stop
        self.title  = title
        self.page   = 0
        self.now    = None    # "who played what" line shown on the board
        self._build()

    def pages(self):
        return max(1, math.ceil(len(self.sounds) / SOUNDS_PER_PAGE))

    def embed(self):
        embed = discord.Embed(
            title       = self.title,
            description = f"共 **{len(self.sounds)}** 個音效，點按鈕就會播放",
            color       = COLOR_PLAYING,
        )
        if (self.now):
            embed.add_field(name="剛剛播放", value=self.now, inline=False)
        if (self.pages() > 1):
            embed.set_footer(text=f"第 {self.page + 1} / {self.pages()} 頁")
        return embed

    def _build(self):
        self.clear_items()
        start = self.page * SOUNDS_PER_PAGE
        for i, (label, file) in enumerate(self.sounds[start:start + SOUNDS_PER_PAGE]):
            button = discord.ui.Button(label=shorten(label, 80), style=discord.ButtonStyle.secondary,
                                       row=i // SOUNDS_PER_ROW)
            button.callback = self._player(label, file)
            self.add_item(button)

        row = SOUND_ROWS
        if (self.pages() > 1):
            self._control("◀️", None, self._prev_page, row, disabled=self.page == 0)
            self._control(None, f"{self.page + 1}/{self.pages()}", None, row, disabled=True)
            self._control("▶️", None, self._next_page, row, disabled=self.page >= self.pages() - 1)
        self._control("🎲", "隨機", self._random, row)
        self._control("⏹️", "停止", self._stop, row, style=discord.ButtonStyle.danger)

    def _control(self, emoji, label, callback, row, disabled=False, style=discord.ButtonStyle.primary):
        button = discord.ui.Button(emoji=emoji, label=label, style=style, row=row, disabled=disabled)
        if (callback):
            button.callback = callback
        self.add_item(button)

    def _player(self, label, file):
        async def callback(interaction):
            await self._play(interaction, label, file)
        return callback

    async def _play(self, interaction, label, file):
        await interaction.response.defer()
        error = await self.play(interaction, file)
        if (error):
            await interaction.followup.send(embed=error_embed(error), ephemeral=True)
            return
        self.now = f"🔊 **{discord.utils.escape_markdown(label)}** · {interaction.user.mention}"
        await interaction.edit_original_response(embed=self.embed(), view=self)

    async def _random(self, interaction):
        label, file = random.choice(self.sounds)
        await self._play(interaction, label, file)

    async def _stop(self, interaction):
        error = await self.stop_(interaction)
        if (error):
            await interaction.response.send_message(embed=error_embed(error), ephemeral=True)
        else:
            await interaction.response.defer()

    async def _prev_page(self, interaction):
        self.page = max(0, self.page - 1)
        self._build()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    async def _next_page(self, interaction):
        self.page = min(self.pages() - 1, self.page + 1)
        self._build()
        await interaction.response.edit_message(embed=self.embed(), view=self)

    async def on_error(self, error, item, interaction):
        logger.error(f"[*] soundboard button failed : {error}")
