# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

歐陽小俠 (Xiao-Xia) is a Discord bot built with [py-cord](https://github.com/Pycord-Development/pycord). It provides music playback, soundboard, AI chat, weather/earthquake alerts (Taiwan-focused), and utility commands.

## Setup

Requires Python 3.11+, ffmpeg on PATH, and a `.env` file (copy from `.env_example`) with:
- `DISCORD_TOKEN` — Discord bot token

Install dependencies with `uv` (preferred) or `pipenv`:
```shell
uv sync
# or
pipenv install
```

## Running

```shell
# Direct run
python main.py

# Auto-restart on git pull (production mode)
python LCCD.py

# Docker
docker build -t discordbot .
docker run -d discordbot
```

## Tests

```shell
pytest test/
# Run a single test
pytest test/test_ai.py::test_wesai -v
```

Note: tests use `pytest-asyncio`; async tests require `@pytest.mark.asyncio`.

## Architecture

### Entry Points
- **`main.py`** — bot entry point; registers cog extensions from `functions/`, starts background loops (`StartChecking`, `EEWLoop`)
- **`LCCD.py`** — production wrapper that auto-restarts `main.py` when git detects upstream changes

### Extension Cogs (`functions/`)
Each `.py` file is loaded as a `bot.load_extension("functions.<name>")` cog at startup. Key cogs:
- `PlayMusic.py` — `/play`, `/skip`, `/pause`, `/list`, `/loop`, `/clear`, `/leave`, playlist management
- `sounds.py` — `/upload_sound`, `/list_sound`, `/search_sound`, `/say`, `/autosound`
- `weather.py` — Taiwan weather commands via CWA API
- `earthquake_alert.py` — `/eew_alert` channel registration
- `Silience.py` — `/silence`, `/talk` per-channel chat toggle
- `SummaryThesis.py` — `/summaryPdf`
- `vote.py`, `roll.py`, `morse.py`, `ping.py`, `Other.py` — utility commands

### Utility Modules (`utils/`)
- **`info.py`** — global state (dicts for `music_user`, `sound_user`, `chat_dict`), file path constants, bot help text, and the shared `logger`
- **`MusicBot.py`** — `MusicBot` class managing per-channel music queue, download (yt-dlp → pytube fallback), FFmpeg playback, state machine (`0=idle`, `1=playing`, `2=paused`, `3=needs_next`)
- **`Chat.py`** — `Chat` class for per-channel conversation with rolling memory (deque of last N messages), backed by `data/message/<channel_id>.txt`
- **`wesAi.py`** — LLM wrapper (Google Generative AI / Gemini) used for chat responses
- **`OnMessage.py`** — `on_message` handler: feeds messages to `Chat` and `recomm`
- **`check.py`** — `StartChecking` background loop (every 30 min) to clean up idle music/sound bots; `EEWLoop` for earthquake early warning via WebSocket streams (TW, JP, FJ regions)
- **`eew.py`** — `EEW` class: WebSocket client for earthquake early warning data
- **`GrabYtList.py`** — YouTube playlist/search grabbing (pytube + yt-dlp)
- **`yt_music_grabber.py`** — `YouTubeDownloader` async downloader
- **`taiwan_map.py`** — map rendering for earthquake alerts (cartopy)
- **`recomm.py`** — per-guild message recommendation tracking

### Data Storage (`data/`)
Flat-file persistence:
- `silence_channel.txt`, `talk_channel.txt` — channel IDs (one per line, int)
- `alert_channel.txt` — channels registered for EEW alerts
- `music/` — cached downloaded audio files (named by song title)
- `message/<channel_id>.txt` — chat history per channel
- `playlist/` — saved playlists
- `record/` — voice recordings

### State Management
Global dicts in `utils/info.py` are the runtime state:
- `music_user[channel_id]` → `MusicBot` instance
- `sound_user[channel_id]` → sound bot instance
- `chat_dict[channel_id]` → `Chat` instance
- `recording[guild_id]` → recording instance

`MusicBot` downloads songs to `data/music/` before playback; filenames are stripped of special characters (`\ / " ' : |`). Music is normalized to -20 dBFS via pydub.
