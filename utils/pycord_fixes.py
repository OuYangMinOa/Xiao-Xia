"""Patches for py-cord bugs that break voice playback.

Imported for its side effects by utils/MusicBot.py, before any voice client is created.
"""
from discord.voice.client import VoiceClient


def _remove_ssrc(self, *, user_id):
    # py-cord (2.8.0rc1 - 2.8.1) assumes a receive reader exists, which is only
    # true while recording. Without one, a member leaving the voice channel raises
    # AttributeError inside the voice websocket poller and kills it: the client
    # still reports is_connected(), but stops handling voice gateway messages and
    # plays audio nobody can hear.
    ssrc = self._id_to_ssrc.pop(user_id, None)
    if ssrc:
        if self._reader:
            self._reader.speaking_timer.drop_ssrc(ssrc)
        self._ssrc_to_id.pop(ssrc, None)


VoiceClient._remove_ssrc = _remove_ssrc
