"""Loudness normalization applied at playback time (EBU R128 / LUFS).

Each file is measured once with ffmpeg's ebur128 filter and the result is
cached in `data/loudness.json`. When a file is played, the gain needed to
reach TARGET_LUFS is passed to the playback ffmpeg as an audio filter, so
songs and sound clips come out at the same perceived loudness without
re-encoding (or decoding into memory) the files themselves.
"""
from utils.info import logger

import asyncio
import json
import os
import re


TARGET_LUFS     = -18.0   # perceived loudness every file is brought to
MAX_BOOST_DB    = 12.0    # don't blow up very quiet clips / background noise
MAX_CUT_DB      = -30.0
SILENCE_LUFS    = -60.0   # quieter than this is treated as silence, left as is
LIMIT_DBFS      = -1.0    # peaks above this after the gain go through a limiter
MEASURE_TIMEOUT = 8       # seconds playback waits for a measurement
CACHE_PATH      = "data/loudness.json"

_cache   = None           # abspath -> {"size", "mtime", "lufs", "peak"}
_pending = {}             # abspath -> measuring Task, so a file is measured once at a time
_measure_slots = asyncio.Semaphore(2)   # each measurement is an ffmpeg process; keep RAM low


def _load_cache():
    global _cache
    if (_cache is None):
        try:
            with open(CACHE_PATH, encoding="utf-8") as f:
                _cache = json.load(f)
        except (OSError, ValueError):
            _cache = {}
    return _cache

def _save_cache():
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    tmp_path = CACHE_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(_cache, f, ensure_ascii=False)
    os.replace(tmp_path, CACHE_PATH)

def _cached(path):
    """Cached measurement for path, or None if missing / the file changed since."""
    entry = _load_cache().get(os.path.abspath(path))
    if (not entry):
        return None
    st = os.stat(path)
    if (entry["size"] != st.st_size or entry["mtime"] != int(st.st_mtime)):
        return None
    return entry


def parse_ebur128(stderr):
    """Pull (integrated LUFS, true peak dBFS) out of ffmpeg ebur128's summary."""
    lufs = re.findall(r"^\s*I:\s+(-?(?:[\d.]+|inf)) LUFS", stderr, re.M)
    peak = re.findall(r"^\s*Peak:\s+(-?(?:[\d.]+|inf)) dBFS", stderr, re.M)
    if (not lufs):
        return None, None
    return float(lufs[-1]), (float(peak[-1]) if peak else None)

def build_filter(lufs, peak):
    """ffmpeg -af value that brings a file at `lufs` to TARGET_LUFS, or None."""
    if (lufs is None or lufs < SILENCE_LUFS):
        return None
    gain = min(MAX_BOOST_DB, max(MAX_CUT_DB, TARGET_LUFS - lufs))
    af   = f"volume={gain:.1f}dB"
    if (peak is None or peak + gain > LIMIT_DBFS):
        # boosting a clip with loud peaks would clip; soft-limit them instead
        af += f",alimiter=limit={10 ** (LIMIT_DBFS / 20):.3f}:level=disabled"
    return af


async def measure(path):
    """Run ffmpeg's ebur128 analysis on path. Returns (lufs, peak) or (None, None)."""
    async with _measure_slots:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-i", path,
            "-map", "0:a:0", "-af", "ebur128=peak=true:framelog=verbose",
            "-f", "null", "-",
            stdout = asyncio.subprocess.DEVNULL,
            stderr = asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
    return parse_ebur128(stderr.decode("utf-8", "ignore"))

async def _measure_and_store(path):
    key = os.path.abspath(path)
    try:
        st = os.stat(path)
        lufs, peak = await measure(path)
        if (lufs is None):
            logger.error(f"[*] loudness : could not measure {path}")
            return None
        entry = {"size": st.st_size, "mtime": int(st.st_mtime), "lufs": lufs, "peak": peak}
        _load_cache()[key] = entry
        _save_cache()
        logger.info(f"[*] loudness : {lufs} LUFS, peak {peak} dBFS - {path}")
        return entry
    except Exception as e:
        logger.error(f"[*] loudness : measuring {path} failed : {e}")
        return None
    finally:
        _pending.pop(key, None)

async def get_filter(path, timeout=MEASURE_TIMEOUT):
    """The -af value to play `path` at TARGET_LUFS, or None to play it as is.

    Uses the cached measurement when there is one. Otherwise measures the file,
    waiting at most `timeout` seconds (None = no limit); a longer measurement
    keeps running in the background so the next play of the file is normalized.
    """
    try:
        entry = _cached(path)
        if (entry is None):
            key  = os.path.abspath(path)
            task = _pending.get(key)
            if (task is None):
                task = _pending[key] = asyncio.create_task(_measure_and_store(path))
            entry = await asyncio.wait_for(asyncio.shield(task), timeout)
    except asyncio.TimeoutError:
        logger.info(f"[*] loudness : still measuring {path}, playing without normalization")
        return None
    except OSError as e:
        logger.error(f"[*] loudness : {e}")
        return None
    if (entry is None):
        return None
    return build_filter(entry["lufs"], entry["peak"])
