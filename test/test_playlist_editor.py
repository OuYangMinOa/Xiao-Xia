import asyncio
import types

import pytest

import utils.playlist_editor as editor_mod
from utils.playlist_editor import PlaylistEditor, SavedPlaylistSource, LiveQueueSource, write_playlist, playlist_path
from utils.PlayListSelection import LoadPlaylist
from test.test_music_ui import bot   # noqa: F401  (fixture)


class FakeResponse:
    def __init__(self):
        self.edited, self.sent, self.modal = None, [], None

    async def edit_message(self, embed=None, view=None):
        self.edited = (embed, view)

    async def send_message(self, embed=None, ephemeral=False, **kwargs):
        self.sent.append(embed)

    async def send_modal(self, modal):
        self.modal = modal

    async def defer(self):
        pass


class FakeInteraction:
    def __init__(self, values=None, voice_channel_id=42):
        self.response = FakeResponse()
        self.data     = {"values": values or []}
        voice         = types.SimpleNamespace(channel=types.SimpleNamespace(id=voice_channel_id))
        self.user     = types.SimpleNamespace(voice=voice, mention="<@9>", display_name="wes")
        self.guild    = types.SimpleNamespace(id=7)
        self.redrawn  = None

    async def edit_original_response(self, embed=None, view=None):
        self.redrawn = (embed, view)


@pytest.fixture
def saved(tmp_path, monkeypatch):
    monkeypatch.setattr(editor_mod, "Playlist_folder", str(tmp_path))
    write_playlist(playlist_path(7, "mix"), [("A, with comma", "https://youtu.be/aaaaaaaaaaa"),
                                             ("B", "https://youtu.be/bbbbbbbbbbb"),
                                             ("C", "https://youtu.be/ccccccccccc")])
    return SavedPlaylistSource(7, "mix")


def titles(source):
    return [song[0] for song in source.load()]


@pytest.mark.asyncio
async def test_saved_playlist_editing(saved, monkeypatch):
    editor = PlaylistEditor(saved)
    embed  = editor.render()
    assert "A, with comma" in embed.description            # titles with commas survive the file format

    await editor._on_select(FakeInteraction(["2"]))
    assert editor.selected == (2, ("C", "https://youtu.be/ccccccccccc"))

    await editor._move_up(FakeInteraction())
    assert titles(saved) == ["A, with comma", "C", "B"]
    await editor._move_top(FakeInteraction())
    assert titles(saved) == ["C", "A, with comma", "B"]
    await editor._move_down(FakeInteraction())
    assert titles(saved) == ["A, with comma", "C", "B"]

    interaction = FakeInteraction()
    await editor._remove(interaction)
    assert titles(saved) == ["A, with comma", "B"]
    assert editor.selected[1][0] == "B"                    # next song stays picked
    embed, view = interaction.response.edited
    assert "刪掉了 C" in embed.fields[0].value

    async def fake_resolve(text, limit):
        return [("D", "https://youtu.be/ddddddddddd"), ("E", "https://youtu.be/eeeeeeeeeee")], False, "playlist"
    monkeypatch.setattr(editor_mod.my_mb, "resolve_songs", fake_resolve)
    interaction = FakeInteraction()
    await editor._on_add(interaction, "https://www.youtube.com/playlist?list=x")
    assert titles(saved) == ["A, with comma", "B", "D", "E"]
    assert "加入了 2 首" in interaction.redrawn[0].fields[0].value

    await editor._on_rename(FakeInteraction(), "new / name")
    assert saved.name == "new name" and titles(saved)[0] == "A, with comma"
    assert LoadPlaylist(playlist_path(7, saved.name))

    first = FakeInteraction()
    await editor._delete_playlist(first)                   # asks for confirmation first
    assert saved.guard(None) is None
    second = FakeInteraction()
    await editor._delete_playlist(second)
    assert saved.guard(None) == "這個歌單已經不存在了"
    assert second.response.edited[1] is None


@pytest.mark.asyncio
async def test_editor_pages_fit_discord_limits(saved):
    saved.mutate(lambda songs: songs.extend((f"S{i}", f"https://youtu.be/{i:011d}") for i in range(40)))
    editor = PlaylistEditor(saved)
    editor.render()
    select = editor.children[0]
    assert len(select.options) == editor_mod.PAGE_SIZE
    assert len(editor.children) <= 25
    assert all(len(row) <= 5 for row in _rows(editor))

    editor.page = 4
    embed = editor.render()
    assert "S39" in embed.description and len(embed.description) < 4096


def _rows(view):
    rows = {}
    for item in view.children:
        rows.setdefault(item.row, []).append(item)
    return [items for row, items in rows.items() if row != 0]


@pytest.mark.asyncio
async def test_queue_editing(bot):
    mb = bot
    await mb._next()                                       # Song A playing, B and C queued
    editor = PlaylistEditor(LiveQueueSource(mb))
    embed  = editor.render()
    assert "正在播放" in embed.description and "Song A" in embed.description

    await editor._on_select(FakeInteraction(["1"]))
    await editor._move_top(FakeInteraction())
    assert [s[0] for s in mb.queqed] == ["Song C", "Song B"]
    assert "Song C" in {f.name: f.value for f in mb.panel.embed.fields}["接下來"].split("\n")[0]

    # someone outside the voice channel can't edit
    outsider = FakeInteraction(voice_channel_id=999)
    await editor._remove(outsider)
    assert outsider.response.sent and [s[0] for s in mb.queqed] == ["Song C", "Song B"]

    # the queue moving on doesn't make the selection point at another song
    mb.queqed.pop(0)
    editor.render()
    assert editor.selected is None
    await mb.kill()


@pytest.mark.asyncio
async def test_editor_buttons_are_not_blue(saved):
    import discord
    editor = PlaylistEditor(saved)
    editor.render()
    colors = {item.style for item in editor.children if isinstance(item, discord.ui.Button)}
    assert colors == {discord.ButtonStyle.secondary, discord.ButtonStyle.danger}
