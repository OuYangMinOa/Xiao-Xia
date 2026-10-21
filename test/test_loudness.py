from utils import loudness
import subprocess
import shutil
import pytest


SUMMARY = """
[Parsed_ebur128_0 @ 0x55] Summary:

  Integrated loudness:
    I:          -6.5 LUFS
    Threshold: -16.6 LUFS

  Loudness range:
    LRA:         4.1 LU

  True peak:
    Peak:        2.6 dBFS
"""

def test_parse_ebur128():
    assert loudness.parse_ebur128(SUMMARY) == (-6.5, 2.6)
    assert loudness.parse_ebur128("no summary here") == (None, None)

def test_build_filter():
    # loud song is turned down, peaks end up below the limit -> no limiter
    assert loudness.build_filter(-6.5, 2.6) == "volume=-11.5dB"
    # quiet clip with loud peaks is boosted and soft-limited
    assert loudness.build_filter(-23.0, -4.0).startswith("volume=5.0dB,alimiter=")
    # boost is capped, silence is left alone
    assert loudness.build_filter(-45.0, -30.0).startswith("volume=12.0dB")
    assert loudness.build_filter(-70.0, -87.0) is None
    assert loudness.build_filter(None, None) is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
@pytest.mark.asyncio
async def test_get_filter_measures_and_caches(tmp_path, monkeypatch):
    monkeypatch.setattr(loudness, "CACHE_PATH", str(tmp_path / "loudness.json"))
    monkeypatch.setattr(loudness, "_cache", None)
    tone = tmp_path / "tone.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
                    "-af", "volume=-30dB", str(tone)], check=True)

    af = await loudness.get_filter(str(tone), timeout=None)
    assert af and af.startswith("volume=")
    assert loudness._cached(str(tone)) is not None
    assert (tmp_path / "loudness.json").is_file()
