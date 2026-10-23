from types import SimpleNamespace

from discord.utils import MISSING
from discord.voice.client import VoiceClient

import utils.pycord_fixes  # noqa: F401


def fake_client(reader=MISSING):
    return SimpleNamespace(_reader=reader, _id_to_ssrc={42: 1234}, _ssrc_to_id={1234: 42})


def test_member_leaving_without_recording_does_not_raise():
    client = fake_client()
    VoiceClient._remove_ssrc(client, user_id=42)
    assert client._id_to_ssrc == {} and client._ssrc_to_id == {}


def test_member_leaving_while_recording_drops_speaking_state():
    dropped = []
    reader  = SimpleNamespace(speaking_timer=SimpleNamespace(drop_ssrc=dropped.append))
    client  = fake_client(reader)
    VoiceClient._remove_ssrc(client, user_id=42)
    assert dropped == [1234] and client._ssrc_to_id == {}


def test_unknown_member_is_ignored():
    client = fake_client()
    VoiceClient._remove_ssrc(client, user_id=7)
    assert client._id_to_ssrc == {42: 1234}
