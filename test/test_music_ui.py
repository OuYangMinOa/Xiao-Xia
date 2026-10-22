import asyncio
import itertools
import types

import discord
import pytest

import utils.MusicBot as my_mb
import utils.music_ui as music_ui


# ------------------------------------------------------------------ helpers

def test_fmt_time():
    assert music_ui.fmt_time(0) == "0:00"
    assert music_ui.fmt_time(65) == "1:05"
    assert music_ui.fmt_time(3725) == "1:02:05"
    assert music_ui.fmt_time(None) == "0:00"

def test_progress_bar():
    assert music_ui.progress_bar(0, 100, 10) == "▱" * 10
    assert music_ui.progress_bar(50, 100, 10) == "▰" * 5 + "▱" * 5
    assert music_ui.progress_bar(500, 100, 10) == "▰" * 10
    assert music_ui.progress_bar(10, None, 10) == "▱" * 10

def test_thumbnail_url():
    assert music_ui.thumbnail_url("https://www.youtube.com/watch?v=fmI_Ndrxy14&list=PLx") \
        == "https://i.ytimg.com/vi/fmI_Ndrxy14/hqdefault.jpg"
    assert music_ui.thumbnail_url("https://youtu.be/fmI_Ndrxy14") \
        == "https://i.ytimg.com/vi/fmI_Ndrxy14/hqdefault.jpg"
    assert music_ui.thumbnail_url("no url") is None
    assert music_ui.thumbnail_url("") is None

def test_song_link_escapes_title():
    link = music_ui.song_link("a [b] *c*", "https://youtu.be/fmI_Ndrxy14")
    assert link.startswith("[a ［b］ \\*c\\*](")
    assert music_ui.song_link("local.mp3", "no url") == "local.mp3"
    assert music_ui.song_link("Tom &amp; Jerry", "") == "Tom & Jerry"


def test_views_dont_override_pycord_view_methods():
    # py-cord calls View.refresh(components) on send / edit; overriding it broke the panel
    from utils.playlist_editor import PlaylistEditor
    base = set(dir(discord.ui.View)) - {"interaction_check", "on_error", "on_timeout"}
    for cls in (music_ui.PlayerView, music_ui.SoundboardView, PlaylistEditor):
        clashes = {name for name in vars(cls) if name in base and not name.startswith("__")}
        assert not clashes, f"{cls.__name__} overrides {clashes}"


# ------------------------------------------------------------------ fake discord

_ids = itertools.count(1000)

def echo_components(view):
    """Like py-cord's send() / edit(): hand the view back the components Discord stored."""
    if (view is not None):
        view.refresh([discord.components._component_factory(row) for row in view.to_components()])

class FakeMessage:
    def __init__(self, channel, embed, view):
        self.id, self.channel, self.embed, self.view = next(_ids), channel, embed, view
        self.deleted = False

    async def edit(self, embed=None, view=None):
        self.embed, self.view = embed, view
        echo_components(view)

    async def delete(self):
        self.deleted = True


class FakeChannel:
    def __init__(self):
        self.id = 1
        self.sent = []
        self.last_message_id = None

    async def send(self, content=None, embed=None, view=None, delete_after=None):
        message = FakeMessage(self, embed, view)
        echo_components(view)
        self.sent.append(message)
        self.last_message_id = message.id
        return message


class FakeVoice:
    def __init__(self):
        self.playing, self.paused, self.after = False, False, None

    def play(self, source, after=None):
        self.playing, self.paused, self.after = True, False, after

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def is_playing(self):
        return self.playing and not self.paused

    def is_connected(self):
        return True


@pytest.fixture
def bot(tmp_path, monkeypatch):
    # cached songs, so _next never downloads
    for name in ("Song A", "Song B", "Song C"):
        (tmp_path / name).write_bytes(b"x")

    monkeypatch.setattr(my_mb.discord, "FFmpegPCMAudio", lambda *a, **k: types.SimpleNamespace())
    monkeypatch.setattr(my_mb.loudness, "get_filter", lambda path: asyncio.sleep(0, None))
    monkeypatch.setattr(my_mb, "probe_duration", lambda path: asyncio.sleep(0, 200.0))

    voice   = FakeVoice()
    channel = FakeChannel()
    guild   = types.SimpleNamespace(id=7, voice_client=voice)
    ctx     = types.SimpleNamespace(channel=channel, guild=guild)
    client  = types.SimpleNamespace(voice_clients=[voice], loop=None)
    vc      = types.SimpleNamespace(id=42, voice_states={})

    mb = my_mb.MusicBot(vc, voice, ctx, client)
    mb.floder = str(tmp_path)
    mb.queqed = [("Song A", "https://youtu.be/aaaaaaaaaaa"),
                 ("Song B", "https://youtu.be/bbbbbbbbbbb"),
                 ("Song C", "https://youtu.be/ccccccccccc")]
    mb.requesters["https://youtu.be/aaaaaaaaaaa"] = "<@1>"
    return mb


def panel_of(mb):
    return mb.panel.embed


@pytest.mark.asyncio
async def test_player_panel_flow(bot):
    mb = bot
    await mb._next()
    assert mb.state == 1 and mb.ui_status == "playing"
    embed = panel_of(mb)
    assert embed.title == "Song A"
    assert embed.author.name == "🎶 正在播放"
    assert "3:20" in embed.description                       # duration from probe_duration
    assert embed.thumbnail.url == "https://i.ytimg.com/vi/aaaaaaaaaaa/hqdefault.jpg"
    fields = {f.name: f.value for f in embed.fields}
    assert fields["點播"] == "<@1>" and fields["順序"] == "1 / 3"
    assert "Song B" in fields["接下來"] and "Song C" in fields["接下來"]
    assert isinstance(mb.view, music_ui.PlayerView)
    assert mb.view.prev_button.disabled                      # nothing before the first song

    # pause edits the same message
    first_panel = mb.panel
    await mb.toggle_pause()
    assert mb.state == 2 and mb.voice.paused
    assert mb.panel is first_panel
    assert panel_of(mb).author.name == "⏸️ 已暫停"
    assert mb.view.toggle_button.emoji.name == "▶️"
    await mb.toggle_pause()
    assert mb.state == 1 and not mb.voice.paused

    # skipping while the panel is still the newest message edits it in place
    await mb.skip()
    assert panel_of(mb).title == "Song B"
    assert mb.panel is first_panel

    # once someone talks, the next song re-posts the panel at the bottom
    await mb.ctx.channel.send("hello")
    await mb.skip()
    assert panel_of(mb).title == "Song C"
    assert first_panel.deleted and mb.panel is not first_panel
    assert mb.ctx.channel.last_message_id == mb.panel.id

    await mb.previous()
    assert panel_of(mb).title == "Song B"
    assert [s[0] for s in mb.queqed] == ["Song C"]

    # queue runs out -> idle panel without buttons
    await mb.skip()
    await mb.skip()
    assert mb.state == 0 and mb.ui_status == "idle"
    assert panel_of(mb).title == "🎵 播放完畢"
    assert mb.panel.view is None

    await mb.kill()
    assert mb.panel is None and not mb.live


@pytest.mark.asyncio
async def test_position_and_resume(bot):
    mb = bot
    await mb._next()
    mb._pos_base, mb._play_t0 = 30, None      # pretend 30s in, paused
    assert mb.startTime == 30
    mb.startTime = 95                         # what /say and the soundboard do
    assert mb.resume_at == 95 and mb.position() == 95
    await mb.skip()
    assert mb.resume_at == 0                  # consumed by the song that just started
    assert mb.position() < 96
    await mb.kill()


@pytest.mark.asyncio
async def test_soundboard_pages():
    labels = [f"s{i}" for i in range(45)]
    board  = music_ui.SoundboardView(labels, [l + ".mp3" for l in labels], play=None, stop=None)
    assert board.pages() == 3
    sound_buttons = [c for c in board.children if c.row < music_ui.SOUND_ROWS]
    assert len(sound_buttons) == music_ui.SOUNDS_PER_PAGE
    assert len(board.children) <= 25

    board.page = 2
    board._build()
    sound_buttons = [c for c in board.children if c.row < music_ui.SOUND_ROWS]
    assert [b.label for b in sound_buttons] == labels[40:]


def test_added_embed():
    member = types.SimpleNamespace(display_name="wes", display_avatar=types.SimpleNamespace(url="https://x/a.png"))
    embed = music_ui.added_embed({"kind": "single", "title": "T", "url": "https://youtu.be/aaaaaaaaaaa", "position": 3}, member)
    assert "第 **3** 首" in embed.description
    embed = music_ui.added_embed({"kind": "playlist", "count": 10, "more": True,
                                  "first": ("First", "https://youtu.be/aaaaaaaaaaa")}, member)
    assert "10" in embed.description and "背景" in embed.description


@pytest.mark.asyncio
async def test_panel_errors_dont_stop_playback(bot, monkeypatch):
    mb = bot
    def broken(_):
        raise TypeError("ui bug")
    monkeypatch.setattr(music_ui, "player_embed", broken)
    await mb._safe_next()
    assert mb.voice.is_playing() and mb.state == 1
    await mb.kill()
