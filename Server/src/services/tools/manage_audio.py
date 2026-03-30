from typing import Annotated, Any, Literal

from fastmcp import Context
from mcp.types import ToolAnnotations

from services.registry import mcp_for_unity_tool
from services.tools import get_unity_instance_from_context
from transport.unity_transport import send_with_unity_instance
from transport.legacy.unity_connection import async_send_command_with_retry

# All possible actions grouped by category
SETUP_ACTIONS = ["ping", "get_audio_info"]

SOURCE_ACTIONS = [
    "add_audio_source",
    "configure_audio_source",
    "remove_audio_source",
]

PLAYBACK_ACTIONS = [
    "play",
    "stop",
    "pause",
    "unpause",
    "play_clip_at_point",
]

CLIP_ACTIONS = [
    "set_clip",
    "get_clip_info",
    "configure_import",
]

LISTENER_ACTIONS = [
    "ensure_listener",
    "configure_listener",
]

ENVIRONMENT_ACTIONS = [
    "add_reverb_zone",
    "configure_reverb_zone",
]

MIXER_ACTIONS = [
    "find_mixers",
    "get_mixer_info",
    "set_mixer_float",
    "get_mixer_float",
    "transition_to_snapshot",
    "set_group_output",
]

ALL_ACTIONS = (
    SETUP_ACTIONS
    + SOURCE_ACTIONS
    + PLAYBACK_ACTIONS
    + CLIP_ACTIONS
    + LISTENER_ACTIONS
    + ENVIRONMENT_ACTIONS
    + MIXER_ACTIONS
)


@mcp_for_unity_tool(
    group="core",
    description=(
        "Manage Unity audio: AudioSource, AudioClip, playback, AudioListener, and AudioReverbZone.\n\n"
        "SETUP:\n"
        "- ping: Check tool availability\n"
        "- get_audio_info: List all AudioSources in the scene with their state\n\n"
        "AUDIOSOURCE:\n"
        "- add_audio_source: Add an AudioSource component to a GameObject\n"
        "- configure_audio_source: Edit AudioSource properties "
        "(volume, pitch, loop, playOnAwake, spatialBlend, minDistance, maxDistance, "
        "rolloffMode, priority, panStereo, dopplerLevel, spread, mute, bypassEffects, "
        "bypassListenerEffects, bypassReverbZones, outputAudioMixerGroup)\n"
        "- remove_audio_source: Remove AudioSource from a GameObject\n\n"
        "PLAYBACK (effective in Play Mode; returns warning in Edit Mode):\n"
        "- play: Play the AudioSource\n"
        "- stop: Stop the AudioSource\n"
        "- pause: Pause the AudioSource\n"
        "- unpause: Unpause the AudioSource\n"
        "- play_clip_at_point: Play a clip one-shot at a world position "
        "(properties: clipPath, position [x,y,z], volume)\n\n"
        "CLIP:\n"
        "- set_clip: Assign an AudioClip asset to an AudioSource (clip_path required)\n"
        "- get_clip_info: Get AudioClip info (length, channels, frequency, samples, loadType)\n"
        "- configure_import: Edit AudioImporter settings "
        "(forceToMono, loadInBackground, preloadAudioData, compressionFormat, quality, "
        "sampleRateSetting)\n\n"
        "LISTENER:\n"
        "- ensure_listener: Verify/create AudioListener in scene (one per scene)\n"
        "- configure_listener: Configure AudioListener (volume, pause)\n\n"
        "ENVIRONMENT:\n"
        "- add_reverb_zone: Add AudioReverbZone to a GameObject (properties: reverbPreset)\n"
        "- configure_reverb_zone: Configure AudioReverbZone "
        "(reverbPreset, minDistance, maxDistance, and custom parameters)\n\n"
        "AUDIOMIXER:\n"
        "- find_mixers: Find all AudioMixer assets in the project\n"
        "- get_mixer_info: Get groups, snapshots and exposed parameters of a mixer "
        "(mixer_path required)\n"
        "- set_mixer_float: Set an exposed float parameter on a mixer "
        "(mixer_path, properties: paramName, value)\n"
        "- get_mixer_float: Get an exposed float parameter from a mixer "
        "(mixer_path, properties: paramName)\n"
        "- transition_to_snapshot: Transition to a named snapshot — Play Mode only "
        "(mixer_path, properties: snapshotName, timeToReach)\n"
        "- set_group_output: Assign an AudioSource to a mixer group "
        "(target, mixer_path, properties: group)\n"
    ),
    annotations=ToolAnnotations(
        title="Manage Audio",
        destructiveHint=True,
    ),
)
async def manage_audio(
    ctx: Context,
    action: Annotated[str, "The audio action to perform."],
    target: Annotated[str | None, "Target GameObject (name, path, or instance ID)."] = None,
    search_method: Annotated[
        Literal["by_id", "by_name", "by_path", "by_tag", "by_layer"] | None,
        "How to find the target.",
    ] = None,
    clip_path: Annotated[
        str | None,
        "Assets path to the AudioClip (e.g. 'Assets/Audio/music.mp3').",
    ] = None,
    mixer_path: Annotated[
        str | None,
        "Assets path to the AudioMixer (e.g. 'Assets/Audio/MainMixer.mixer').",
    ] = None,
    properties: Annotated[
        dict[str, Any] | str | None,
        "Action-specific parameters (dict or JSON string).",
    ] = None,
) -> dict[str, Any]:
    """Unified audio management tool for Unity AudioSource, AudioClip, AudioListener, and AudioReverbZone."""

    action_normalized = action.lower()

    if action_normalized not in ALL_ACTIONS:
        categories = {
            "Setup": SETUP_ACTIONS,
            "AudioSource": SOURCE_ACTIONS,
            "Playback": PLAYBACK_ACTIONS,
            "Clip": CLIP_ACTIONS,
            "Listener": LISTENER_ACTIONS,
            "Environment": ENVIRONMENT_ACTIONS,
            "Mixer": MIXER_ACTIONS,
        }
        category_list = "; ".join(
            f"{cat}: {', '.join(actions)}" for cat, actions in categories.items()
        )
        return {
            "success": False,
            "message": (
                f"Unknown action '{action}'. Available actions by category — {category_list}."
            ),
        }

    unity_instance = await get_unity_instance_from_context(ctx)

    params_dict: dict[str, Any] = {"action": action_normalized}
    if target is not None:
        params_dict["target"] = target
    if search_method is not None:
        params_dict["searchMethod"] = search_method
    if clip_path is not None:
        params_dict["clipPath"] = clip_path
    if mixer_path is not None:
        params_dict["mixerPath"] = mixer_path
    if properties is not None:
        params_dict["properties"] = properties

    result = await send_with_unity_instance(
        async_send_command_with_retry,
        unity_instance,
        "manage_audio",
        params_dict,
    )

    if not isinstance(result, dict):
        return {"success": False, "message": str(result)}

    return result
