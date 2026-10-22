"""Edit a song list with buttons: a saved playlist (data/playlist/<guild>/<name>.txt)
or the live queue of a MusicBot.

Both kinds of list go through a "source" with the same small interface, so one
PlaylistEditor view drives either of them:

    load()          -> list of (title, url)
    mutate(fn)      -> runs fn(songs) on the list and persists it, returns fn's result
    changed()       -> coroutine, called after a successful edit
    guard(user)     -> None, or the reason this user can't edit right now
"""
import math
import os
from glob import glob

import discord

from utils.info              import logger, Playlist_folder
from utils.music_ui          import (info_embed, error_embed, song_link, shorten, member_name,
                                     COLOR_PLAYING, COLOR_DONE)
from utils.PlayListSelection import LoadPlaylist
import utils.MusicBot as my_mb


PAGE_SIZE      = 10
ADD_SONG_LIMIT = 200      # songs taken from a playlist / album url added to a saved playlist


# ------------------------------------------------------------------ saved playlist files

def playlist_folder(guild_id):
    return os.path.join(Playlist_folder, str(guild_id))

def list_playlists(guild_id):
    return sorted(os.path.basename(path)[:-4] for path in glob(os.path.join(playlist_folder(guild_id), "*.txt")))

def playlist_path(guild_id, name):
    return os.path.join(playlist_folder(guild_id), f"{name}.txt")

def write_playlist(path, songs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # one "title,url" per line; LoadPlaylist splits on the last comma
    lines = [f"{' '.join(str(title).split())},{url}" for title, url in songs]
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    os.replace(tmp_path, path)

def clean_playlist_name(name):
    return my_mb.safe_song_filename(name, fallback="playlist")[:90]


class SavedPlaylistSource:
    kind = "saved"

    def __init__(self, guild_id, name):
        self.guild_id, self.name = guild_id, name

    @property
    def path(self):
        return playlist_path(self.guild_id, self.name)

    @property
    def title(self):
        return f"📂 歌單：{self.name}"

    def guard(self, user):
        if (not os.path.isfile(self.path)):
            return "這個歌單已經不存在了"
        return None

    def load(self):
        return LoadPlaylist(self.path) if os.path.isfile(self.path) else []

    def mutate(self, fn):
        songs  = self.load()
        result = fn(songs)
        write_playlist(self.path, songs)
        return result

    async def changed(self):
        pass

    def rename(self, new_name):
        new_path = playlist_path(self.guild_id, new_name)
        if (os.path.exists(new_path)):
            raise FileExistsError(new_name)
        os.replace(self.path, new_path)
        self.name = new_name

    def delete(self):
        os.remove(self.path)


class LiveQueueSource:
    kind = "queue"

    def __init__(self, mb):
        self.mb = mb

    @property
    def title(self):
        return "📜 播放清單"

    def guard(self, user):
        if (not self.mb.live):
            return "播放器已經關閉了，用 `/play` 重新開始"
        voice = getattr(user, "voice", None)
        if (voice is None or voice.channel is None or voice.channel.id != self.mb.channelid):
            return "要跟我在同一個語音頻道才能改清單喔"
        return None

    def load(self):
        # always read the attribute: clear() and loop replace the list object
        return self.mb.queqed

    def mutate(self, fn):
        return fn(self.mb.queqed)

    async def changed(self):
        await self.mb.update_panel()


# ------------------------------------------------------------------ modals

class _TextModal(discord.ui.Modal):
    def __init__(self, title, label, on_submit, placeholder=None, value=None, max_length=200):
        super().__init__(title=title)
        self.on_submit = on_submit
        self.add_item(discord.ui.InputText(label=label, placeholder=placeholder, value=value,
                                           max_length=max_length))

    async def callback(self, interaction):
        await self.on_submit(interaction, self.children[0].value.strip())


# ------------------------------------------------------------------ the editor

class PlaylistEditor(discord.ui.View):
    """Ephemeral editor: pick a song in the select, then move / remove it with buttons.

    Args:
        source: a SavedPlaylistSource or LiveQueueSource
        play_saved: coroutine (interaction, name, songs) -> error str or None, used by
            the "play this playlist" button of a saved playlist
    """

    def __init__(self, source, play_saved=None):
        # ephemeral messages can only be edited for 15 minutes
        super().__init__(timeout=14 * 60, disable_on_timeout=True)
        self.source         = source
        self.play_saved     = play_saved
        self.page           = 0
        self.selected       = None   # (index, (title, url)) of the picked song
        self.status         = ""     # what the last action did, shown on the embed
        self.confirm_delete = False

    # ---------------------------------------------------------- selection

    def _find(self, songs):
        """Index of the selected song in songs (it may have moved), or None."""
        if (self.selected is None):
            return None
        index, song = self.selected
        if (0 <= index < len(songs) and tuple(songs[index]) == song):
            return index
        for i, each in enumerate(songs):
            if (tuple(each) == song):
                self.selected = (i, song)
                return i
        self.selected = None
        return None

    def _select(self, songs, index):
        if (index is None or not (0 <= index < len(songs))):
            self.selected = None
            return
        self.selected = (index, tuple(songs[index]))
        self.page     = index // PAGE_SIZE

    # ---------------------------------------------------------- rendering

    def render(self):
        """Embed for the current state; also rebuilds the components."""
        songs = list(self.source.load())
        index = self._find(songs)
        pages = max(1, math.ceil(len(songs) / PAGE_SIZE))
        self.page = max(0, min(self.page, pages - 1))
        self._build(songs, index, pages)
        return self._embed(songs, index, pages)

    def _embed(self, songs, index, pages):
        lines = []
        if (self.source.kind == "queue"):
            mb, song = self.source.mb, self.source.mb.this_song
            if (mb.state != 0 and song):
                lines.append(f"**正在播放**　{song_link(song[0], song[1], 70)}\n")

        start = self.page * PAGE_SIZE
        for i, each in enumerate(songs[start:start + PAGE_SIZE], start):
            if (i == index):
                lines.append(f"**▶ `{i + 1:>3}.` {song_link(each[0], each[1], 55)}**")
            else:
                lines.append(f"`{i + 1:>5}.` {song_link(each[0], each[1], 55)}")
        if (not songs):
            lines.append("這裡還沒有歌，按 ➕ 加幾首吧！")

        count = f"接下來 {len(songs)} 首" if self.source.kind == "queue" else f"{len(songs)} 首"
        embed = discord.Embed(title=f"{self.source.title} · {count}", description="\n".join(lines), color=COLOR_PLAYING)
        if (self.status):
            embed.add_field(name="剛剛", value=self.status, inline=False)
        hint = "先在選單選一首歌，再按下面的按鈕" if songs else "按 ➕ 加歌"
        embed.set_footer(text=f"第 {self.page + 1} / {pages} 頁 · {hint}")
        return embed

    def _button(self, row, callback, emoji=None, label=None, style=discord.ButtonStyle.secondary, disabled=False):
        button = discord.ui.Button(emoji=emoji, label=label, style=style, row=row, disabled=disabled)
        if (callback):
            button.callback = callback
        self.add_item(button)

    def _build(self, songs, index, pages):
        self.clear_items()
        start = self.page * PAGE_SIZE
        page_songs = songs[start:start + PAGE_SIZE]
        if (page_songs):
            select = discord.ui.Select(
                placeholder = "選一首歌來編輯",
                options = [discord.SelectOption(label=shorten(f"{i + 1}. {each[0]}", 100), value=str(i),
                                                default=(i == index))
                           for i, each in enumerate(page_songs, start)],
                row = 0,
            )
            select.callback = self._on_select
            self.add_item(select)

        none = index is None
        top_label = "下一首播" if self.source.kind == "queue" else "置頂"
        self._button(1, self._move_up,   "⬆️", "上移", disabled=none or index == 0)
        self._button(1, self._move_down, "⬇️", "下移", disabled=none or index == len(songs) - 1)
        self._button(1, self._move_top,  "⏫", top_label, disabled=none or index == 0)
        self._button(1, self._remove,    "🗑️", "刪除", style=discord.ButtonStyle.danger, disabled=none)
        self._button(1, self._add,       "➕", "加歌", style=discord.ButtonStyle.success)

        self._button(2, self._prev_page, "◀️", disabled=self.page == 0)
        self._button(2, None, label=f"{self.page + 1}/{pages}", disabled=True)
        self._button(2, self._next_page, "▶️", disabled=self.page >= pages - 1)
        if (self.source.kind == "saved"):
            self._button(2, self._rename, "✏️", "改名")
            if (self.confirm_delete):
                self._button(2, self._delete_playlist, "⚠️", "確定刪除？", style=discord.ButtonStyle.danger)
            else:
                self._button(2, self._delete_playlist, "❌", "刪除歌單")
            self._button(3, self._play, "▶️", "播放這個歌單", style=discord.ButtonStyle.primary, disabled=not songs)
            self._button(3, self._refresh, "🔄", "重新整理")
        else:
            self._button(2, self._save_as, "💾", "存成歌單")
            self._button(3, self._refresh, "🔄", "重新整理")

    async def _show(self, interaction):
        """Answer a component interaction by redrawing the editor."""
        await interaction.response.edit_message(embed=self.render(), view=self)

    async def _redraw(self, interaction):
        """Redraw after the interaction was already deferred."""
        try:
            await interaction.edit_original_response(embed=self.render(), view=self)
        except discord.HTTPException as e:
            logger.error(f"[*] playlist editor redraw failed : {e}")

    async def on_error(self, error, item, interaction):
        logger.error(f"[*] playlist editor failed : {error}")

    # ---------------------------------------------------------- editing

    async def _edit(self, interaction, fn):
        """Run fn(songs) -> status text on the list, then redraw."""
        reason = self.source.guard(interaction.user)
        if (reason):
            await interaction.response.send_message(embed=error_embed(reason), ephemeral=True)
            return
        self.confirm_delete = False
        try:
            self.status = self.source.mutate(fn) or self.status
        except Exception as e:
            logger.error(f"[*] playlist edit failed : {e}")
            self.status = "⚠️ 改不了，再試一次"
        await self._show(interaction)
        await self.source.changed()

    async def _on_select(self, interaction):
        songs = list(self.source.load())
        index = int(interaction.data["values"][0])
        self._select(songs, index)
        self.confirm_delete = False
        await self._show(interaction)

    async def _move_up(self, interaction):
        def fn(songs):
            i = self._find(songs)
            if (i is None or i == 0):
                return None
            songs[i - 1], songs[i] = songs[i], songs[i - 1]
            self._select(songs, i - 1)
            return f"⬆️ 上移了 {shorten(songs[i - 1][0], 50)}"
        await self._edit(interaction, fn)

    async def _move_down(self, interaction):
        def fn(songs):
            i = self._find(songs)
            if (i is None or i >= len(songs) - 1):
                return None
            songs[i + 1], songs[i] = songs[i], songs[i + 1]
            self._select(songs, i + 1)
            return f"⬇️ 下移了 {shorten(songs[i + 1][0], 50)}"
        await self._edit(interaction, fn)

    async def _move_top(self, interaction):
        def fn(songs):
            i = self._find(songs)
            if (i is None or i == 0):
                return None
            songs.insert(0, songs.pop(i))
            self._select(songs, 0)
            if (self.source.kind == "queue"):
                return f"⏫ {shorten(songs[0][0], 50)} 下一首就播"
            return f"⏫ 把 {shorten(songs[0][0], 50)} 移到最前面"
        await self._edit(interaction, fn)

    async def _remove(self, interaction):
        def fn(songs):
            i = self._find(songs)
            if (i is None):
                return None
            removed = songs.pop(i)
            # keep a song picked so several can be removed in a row
            self._select(songs, i if i < len(songs) else i - 1)
            return f"🗑️ 刪掉了 {shorten(removed[0], 50)}"
        await self._edit(interaction, fn)

    async def _add(self, interaction):
        reason = self.source.guard(interaction.user)
        if (reason):
            await interaction.response.send_message(embed=error_embed(reason), ephemeral=True)
            return
        await interaction.response.send_modal(_TextModal(
            "加歌", "YouTube / Spotify 連結或歌名", self._on_add,
            placeholder="https://www.youtube.com/watch?v=... 或歌名", max_length=400))

    async def _on_add(self, interaction, text):
        await interaction.response.defer()
        if (not text):
            return
        reason = self.source.guard(interaction.user)
        if (reason):
            await interaction.followup.send(embed=error_embed(reason), ephemeral=True)
            return

        if (self.source.kind == "queue"):
            result = await self.source.mb.add(text, requester=interaction.user.mention)
            if (not result["ok"]):
                self.status = f"⚠️ {result['error']}"
            elif (result["kind"] == "playlist"):
                self.status = f"➕ 加入了 {result['count']} 首" + ("，其餘在背景載入" if result.get("more") else "")
            else:
                self.status = f"➕ 加入了 {shorten(result['title'], 50)}"
        else:
            try:
                new_songs, _, _ = await my_mb.resolve_songs(text, limit=ADD_SONG_LIMIT)
            except Exception as e:
                logger.error(f"[*] resolving {text} failed : {e}")
                new_songs = []
            if (not new_songs):
                self.status = "⚠️ 找不到這首歌，換個連結或關鍵字試試"
            else:
                def fn(songs):
                    songs.extend(new_songs)
                    self._select(songs, len(songs) - len(new_songs))
                self.source.mutate(fn)
                if (len(new_songs) == 1):
                    self.status = f"➕ 加入了 {shorten(new_songs[0][0], 50)}"
                else:
                    self.status = f"➕ 加入了 {len(new_songs)} 首"
        await self._redraw(interaction)

    # ---------------------------------------------------------- pages

    async def _prev_page(self, interaction):
        self.page -= 1
        await self._show(interaction)

    async def _next_page(self, interaction):
        self.page += 1
        await self._show(interaction)

    async def _refresh(self, interaction):
        await self._show(interaction)

    # ---------------------------------------------------------- whole playlist

    async def _rename(self, interaction):
        reason = self.source.guard(interaction.user)
        if (reason):
            await interaction.response.send_message(embed=error_embed(reason), ephemeral=True)
            return
        await interaction.response.send_modal(_TextModal("歌單改名", "新的名字", self._on_rename,
                                                         value=self.source.name, max_length=90))

    async def _on_rename(self, interaction, text):
        name = clean_playlist_name(text)
        old  = self.source.name
        if (name != old):
            try:
                self.source.rename(name)
                self.status = f"✏️ 歌單改名成 **{discord.utils.escape_markdown(name)}**"
            except FileExistsError:
                self.status = f"⚠️ 已經有叫 {name} 的歌單了"
            except OSError as e:
                logger.error(f"[*] renaming playlist {old} failed : {e}")
                self.status = "⚠️ 改名失敗，再試一次"
        await self._show(interaction)

    async def _delete_playlist(self, interaction):
        if (not self.confirm_delete):
            self.confirm_delete = True
            self.status = "再按一次「確定刪除？」就會刪掉整個歌單"
            await self._show(interaction)
            return
        try:
            self.source.delete()
        except OSError as e:
            logger.error(f"[*] deleting playlist {self.source.name} failed : {e}")
        self.stop()
        await interaction.response.edit_message(
            embed=info_embed(f"🗑️ 已刪除歌單 **{discord.utils.escape_markdown(self.source.name)}**", COLOR_DONE),
            view=None)

    async def _play(self, interaction):
        await interaction.response.defer()
        songs = self.source.load()
        error = await self.play_saved(interaction, self.source.name, songs) if self.play_saved else "沒辦法從這裡播放"
        self.status = f"⚠️ {error}" if error else "▶️ 開始播放這個歌單"
        await self._redraw(interaction)

    async def _save_as(self, interaction):
        await interaction.response.send_modal(_TextModal("存成歌單", "歌單名字", self._on_save_as, max_length=90))

    async def _on_save_as(self, interaction, text):
        mb    = self.source.mb
        songs = mb.passed + mb.queqed
        if (not songs):
            self.status = "⚠️ 清單是空的，沒東西可以存"
        else:
            name = clean_playlist_name(text)
            write_playlist(playlist_path(interaction.guild.id, name), songs)
            self.status = f"💾 存成歌單 **{discord.utils.escape_markdown(name)}**（{len(songs)} 首）"
        await self._show(interaction)
