from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from services.tools.manage_audio import (
    manage_audio,
    ALL_ACTIONS,
    SETUP_ACTIONS,
    SOURCE_ACTIONS,
    PLAYBACK_ACTIONS,
    CLIP_ACTIONS,
    LISTENER_ACTIONS,
    ENVIRONMENT_ACTIONS,
    MIXER_ACTIONS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_unity(monkeypatch):
    """Patch Unity transport layer and return captured call dict."""
    captured: dict[str, object] = {}

    async def fake_send(send_fn, unity_instance, tool_name, params):
        captured["unity_instance"] = unity_instance
        captured["tool_name"] = tool_name
        captured["params"] = params
        return {"success": True, "message": "ok"}

    monkeypatch.setattr(
        "services.tools.manage_audio.get_unity_instance_from_context",
        AsyncMock(return_value="unity-instance-1"),
    )
    monkeypatch.setattr(
        "services.tools.manage_audio.send_with_unity_instance",
        fake_send,
    )
    return captured


# ---------------------------------------------------------------------------
# Action list completeness
# ---------------------------------------------------------------------------

def test_all_actions_is_union_of_sub_lists():
    expected = set(
        SETUP_ACTIONS + SOURCE_ACTIONS + PLAYBACK_ACTIONS
        + CLIP_ACTIONS + LISTENER_ACTIONS + ENVIRONMENT_ACTIONS
        + MIXER_ACTIONS
    )
    assert set(ALL_ACTIONS) == expected


def test_no_duplicate_actions():
    assert len(ALL_ACTIONS) == len(set(ALL_ACTIONS))


def test_all_actions_count():
    assert len(ALL_ACTIONS) == 23


# ---------------------------------------------------------------------------
# Invalid / missing action
# ---------------------------------------------------------------------------

def test_unknown_action_returns_error(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="nonexistent_action")
    )
    assert result["success"] is False
    assert "Unknown action" in result["message"]
    assert "tool_name" not in mock_unity


def test_empty_action_returns_error(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="")
    )
    assert result["success"] is False
    assert "tool_name" not in mock_unity


def test_unknown_action_message_lists_categories(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="dance")
    )
    assert "Setup" in result["message"]
    assert "AudioSource" in result["message"]
    assert "Playback" in result["message"]


# ---------------------------------------------------------------------------
# Setup actions
# ---------------------------------------------------------------------------

def test_ping_sends_correct_params(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="ping")
    )
    assert result["success"] is True
    assert mock_unity["tool_name"] == "manage_audio"
    assert mock_unity["params"]["action"] == "ping"


def test_get_audio_info_sends_correct_action(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="get_audio_info")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "get_audio_info"


# ---------------------------------------------------------------------------
# AudioSource actions
# ---------------------------------------------------------------------------

def test_add_audio_source_with_target(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="add_audio_source",
            target="Player",
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "add_audio_source"
    assert mock_unity["params"]["target"] == "Player"


def test_add_audio_source_with_properties(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="add_audio_source",
            target="MusicPlayer",
            properties={"volume": 0.8, "loop": True},
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["properties"]["volume"] == 0.8
    assert mock_unity["params"]["properties"]["loop"] is True


def test_configure_audio_source_sends_properties(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="configure_audio_source",
            target="SFX",
            properties={
                "volume": 0.5,
                "pitch": 1.2,
                "spatialBlend": 1.0,
                "minDistance": 2.0,
                "maxDistance": 30.0,
                "rolloffMode": "Logarithmic",
                "loop": False,
                "playOnAwake": True,
                "priority": 64,
                "panStereo": -0.5,
                "dopplerLevel": 0.0,
                "spread": 45.0,
                "mute": False,
            },
        )
    )
    assert result["success"] is True
    props = mock_unity["params"]["properties"]
    assert props["volume"] == 0.5
    assert props["pitch"] == 1.2
    assert props["spatialBlend"] == 1.0
    assert props["rolloffMode"] == "Logarithmic"
    assert props["priority"] == 64


def test_remove_audio_source_sends_target(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="remove_audio_source",
            target="OldSFX",
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "remove_audio_source"
    assert mock_unity["params"]["target"] == "OldSFX"


# ---------------------------------------------------------------------------
# Playback actions
# ---------------------------------------------------------------------------

def test_play_sends_target(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="play", target="MusicPlayer")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "play"
    assert mock_unity["params"]["target"] == "MusicPlayer"


def test_stop_sends_target(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="stop", target="MusicPlayer")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "stop"
    assert mock_unity["params"]["target"] == "MusicPlayer"


def test_pause_sends_target(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="pause", target="Ambient")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "pause"


def test_unpause_sends_target(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="unpause", target="Ambient")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "unpause"


def test_play_clip_at_point_sends_properties(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="play_clip_at_point",
            properties={
                "clipPath": "Assets/Audio/boom.wav",
                "position": [1.0, 0.0, 5.0],
                "volume": 0.9,
            },
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "play_clip_at_point"
    assert mock_unity["params"]["properties"]["clipPath"] == "Assets/Audio/boom.wav"


# ---------------------------------------------------------------------------
# Clip actions
# ---------------------------------------------------------------------------

def test_set_clip_sends_clip_path(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="set_clip",
            target="MusicPlayer",
            clip_path="Assets/Audio/theme.mp3",
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "set_clip"
    assert mock_unity["params"]["clipPath"] == "Assets/Audio/theme.mp3"
    assert mock_unity["params"]["target"] == "MusicPlayer"


def test_get_clip_info_with_clip_path(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="get_clip_info",
            clip_path="Assets/Audio/sfx.wav",
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["clipPath"] == "Assets/Audio/sfx.wav"


def test_get_clip_info_with_target(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="get_clip_info",
            target="SFXSource",
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["target"] == "SFXSource"


def test_configure_import_sends_clip_path_and_properties(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="configure_import",
            clip_path="Assets/Audio/music.mp3",
            properties={
                "forceToMono": False,
                "loadInBackground": True,
                "compressionFormat": "Vorbis",
                "quality": 0.7,
            },
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["clipPath"] == "Assets/Audio/music.mp3"
    assert mock_unity["params"]["properties"]["compressionFormat"] == "Vorbis"


# ---------------------------------------------------------------------------
# Listener actions
# ---------------------------------------------------------------------------

def test_ensure_listener_sends_action(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="ensure_listener")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "ensure_listener"
    assert "target" not in mock_unity["params"]


def test_configure_listener_sends_properties(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="configure_listener",
            properties={"volume": 0.9, "pause": False},
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "configure_listener"
    assert mock_unity["params"]["properties"]["volume"] == 0.9


# ---------------------------------------------------------------------------
# Environment actions
# ---------------------------------------------------------------------------

def test_add_reverb_zone_with_target(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="add_reverb_zone",
            target="Cave",
            properties={"reverbPreset": "Cave"},
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "add_reverb_zone"
    assert mock_unity["params"]["target"] == "Cave"
    assert mock_unity["params"]["properties"]["reverbPreset"] == "Cave"


def test_configure_reverb_zone_sends_properties(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="configure_reverb_zone",
            target="Cave",
            properties={
                "reverbPreset": "Hallway",
                "minDistance": 5.0,
                "maxDistance": 25.0,
            },
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["properties"]["reverbPreset"] == "Hallway"
    assert mock_unity["params"]["properties"]["minDistance"] == 5.0


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------

def test_search_method_passed_through(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="add_audio_source",
            target="12345",
            search_method="by_id",
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["searchMethod"] == "by_id"


def test_search_method_by_path(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="configure_audio_source",
            target="Level/Player/SFX",
            search_method="by_path",
            properties={"volume": 0.5},
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["searchMethod"] == "by_path"


def test_none_params_omitted(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="ping",
            target=None,
            search_method=None,
            clip_path=None,
            properties=None,
        )
    )
    assert result["success"] is True
    assert "target" not in mock_unity["params"]
    assert "searchMethod" not in mock_unity["params"]
    assert "clipPath" not in mock_unity["params"]
    assert "properties" not in mock_unity["params"]


def test_string_properties_passed_through(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="configure_audio_source",
            target="SFX",
            properties='{"volume": 0.5, "loop": true}',
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["properties"] == '{"volume": 0.5, "loop": true}'


def test_non_dict_response_wrapped(monkeypatch):
    """When Unity returns a non-dict, it should be wrapped."""
    monkeypatch.setattr(
        "services.tools.manage_audio.get_unity_instance_from_context",
        AsyncMock(return_value="unity-1"),
    )

    async def fake_send(send_fn, unity_instance, tool_name, params):
        return "unexpected string response"

    monkeypatch.setattr(
        "services.tools.manage_audio.send_with_unity_instance",
        fake_send,
    )

    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="ping")
    )
    assert result["success"] is False
    assert "unexpected string response" in result["message"]


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------

def test_action_case_insensitive(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="Add_Audio_Source", target="Player")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "add_audio_source"


def test_action_uppercase(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="PING")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "ping"


def test_action_mixed_case_playback(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="Play", target="MusicPlayer")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "play"


# ---------------------------------------------------------------------------
# AudioMixer actions
# ---------------------------------------------------------------------------

def test_find_mixers_sends_action(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="find_mixers")
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "find_mixers"
    assert "target" not in mock_unity["params"]
    assert "mixerPath" not in mock_unity["params"]


def test_get_mixer_info_sends_mixer_path(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="get_mixer_info",
            mixer_path="Assets/Audio/MainMixer.mixer",
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "get_mixer_info"
    assert mock_unity["params"]["mixerPath"] == "Assets/Audio/MainMixer.mixer"


def test_set_mixer_float_sends_param_and_value(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="set_mixer_float",
            mixer_path="Assets/Audio/MainMixer.mixer",
            properties={"paramName": "MasterVolume", "value": -10.0},
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["mixerPath"] == "Assets/Audio/MainMixer.mixer"
    assert mock_unity["params"]["properties"]["paramName"] == "MasterVolume"
    assert mock_unity["params"]["properties"]["value"] == -10.0


def test_get_mixer_float_sends_param_name(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="get_mixer_float",
            mixer_path="Assets/Audio/MainMixer.mixer",
            properties={"paramName": "MusicVolume"},
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "get_mixer_float"
    assert mock_unity["params"]["properties"]["paramName"] == "MusicVolume"


def test_transition_to_snapshot_sends_snapshot_name(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="transition_to_snapshot",
            mixer_path="Assets/Audio/MainMixer.mixer",
            properties={"snapshotName": "Quiet", "timeToReach": 1.5},
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "transition_to_snapshot"
    assert mock_unity["params"]["properties"]["snapshotName"] == "Quiet"
    assert mock_unity["params"]["properties"]["timeToReach"] == 1.5


def test_set_group_output_sends_target_mixer_and_group(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="set_group_output",
            target="MusicPlayer",
            mixer_path="Assets/Audio/MainMixer.mixer",
            properties={"group": "Master/Music"},
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "set_group_output"
    assert mock_unity["params"]["target"] == "MusicPlayer"
    assert mock_unity["params"]["mixerPath"] == "Assets/Audio/MainMixer.mixer"
    assert mock_unity["params"]["properties"]["group"] == "Master/Music"


def test_mixer_path_omitted_when_none(mock_unity):
    result = asyncio.run(
        manage_audio(SimpleNamespace(), action="find_mixers", mixer_path=None)
    )
    assert result["success"] is True
    assert "mixerPath" not in mock_unity["params"]


def test_mixer_action_case_insensitive(mock_unity):
    result = asyncio.run(
        manage_audio(
            SimpleNamespace(),
            action="Find_Mixers",
        )
    )
    assert result["success"] is True
    assert mock_unity["params"]["action"] == "find_mixers"
