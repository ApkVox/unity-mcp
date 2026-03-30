"""Audio CLI commands for managing Unity audio via manage_audio tool."""

from typing import Optional, Any

import click

from cli.utils.config import get_config
from cli.utils.output import format_output
from cli.utils.connection import run_command, handle_unity_errors
from cli.utils.constants import SEARCH_METHOD_CHOICE_BASIC


@click.group()
def audio():
    """Audio operations - AudioSource control, audio settings."""
    pass


@audio.command("list")
@handle_unity_errors
def list_sources():
    """List all AudioSources in the scene.

    \b
    Examples:
        unity-mcp audio list
    """
    config = get_config()
    result = run_command("manage_audio", {"action": "get_audio_info"}, config)
    click.echo(format_output(result, config.format))


@audio.command("add")
@click.argument("target")
@click.option("--clip", "-c", default=None, help="AudioClip asset path.")
@click.option("--volume", "-v", type=float, default=None, help="Initial volume (0.0–1.0).")
@click.option("--loop", is_flag=True, default=False, help="Enable looping.")
@click.option(
    "--search-method",
    type=SEARCH_METHOD_CHOICE_BASIC,
    default=None,
    help="How to find the target.",
)
@handle_unity_errors
def add(target: str, clip: Optional[str], volume: Optional[float], loop: bool, search_method: Optional[str]):
    """Add an AudioSource to a GameObject.

    \b
    Examples:
        unity-mcp audio add "Player"
        unity-mcp audio add "MusicPlayer" --clip "Assets/Audio/music.mp3" --loop
        unity-mcp audio add "SFX" --volume 0.8
    """
    config = get_config()

    params: dict[str, Any] = {
        "action": "add_audio_source",
        "target": target,
    }

    if search_method:
        params["searchMethod"] = search_method

    props: dict[str, Any] = {}
    if clip:
        params["clipPath"] = clip
    if volume is not None:
        props["volume"] = volume
    if loop:
        props["loop"] = True
    if props:
        params["properties"] = props

    result = run_command("manage_audio", params, config)
    click.echo(format_output(result, config.format))


@audio.command("play")
@click.argument("target")
@click.option("--clip", "-c", default=None, help="AudioClip asset path to assign before playing.")
@click.option(
    "--search-method",
    type=SEARCH_METHOD_CHOICE_BASIC,
    default=None,
    help="How to find the target.",
)
@handle_unity_errors
def play(target: str, clip: Optional[str], search_method: Optional[str]):
    """Play audio on a target's AudioSource.

    \b
    Examples:
        unity-mcp audio play "MusicPlayer"
        unity-mcp audio play "SFXSource" --clip "Assets/Audio/explosion.wav"
    """
    config = get_config()

    if clip:
        set_params: dict[str, Any] = {
            "action": "set_clip",
            "target": target,
            "clipPath": clip,
        }
        if search_method:
            set_params["searchMethod"] = search_method
        run_command("manage_audio", set_params, config)

    params: dict[str, Any] = {
        "action": "play",
        "target": target,
    }
    if search_method:
        params["searchMethod"] = search_method

    result = run_command("manage_audio", params, config)
    click.echo(format_output(result, config.format))


@audio.command("stop")
@click.argument("target")
@click.option(
    "--search-method",
    type=SEARCH_METHOD_CHOICE_BASIC,
    default=None,
    help="How to find the target.",
)
@handle_unity_errors
def stop(target: str, search_method: Optional[str]):
    """Stop audio on a target's AudioSource.

    \b
    Examples:
        unity-mcp audio stop "MusicPlayer"
    """
    config = get_config()

    params: dict[str, Any] = {
        "action": "stop",
        "target": target,
    }
    if search_method:
        params["searchMethod"] = search_method

    result = run_command("manage_audio", params, config)
    click.echo(format_output(result, config.format))


@audio.command("volume")
@click.argument("target")
@click.argument("level", type=float)
@click.option(
    "--search-method",
    type=SEARCH_METHOD_CHOICE_BASIC,
    default=None,
    help="How to find the target.",
)
@handle_unity_errors
def volume(target: str, level: float, search_method: Optional[str]):
    """Set audio volume on a target's AudioSource.

    \b
    Examples:
        unity-mcp audio volume "MusicPlayer" 0.5
    """
    config = get_config()

    params: dict[str, Any] = {
        "action": "configure_audio_source",
        "target": target,
        "properties": {"volume": level},
    }
    if search_method:
        params["searchMethod"] = search_method

    result = run_command("manage_audio", params, config)
    click.echo(format_output(result, config.format))


@audio.command("info")
@click.argument("target", required=False, default=None)
@click.option(
    "--search-method",
    type=SEARCH_METHOD_CHOICE_BASIC,
    default=None,
    help="How to find the target.",
)
@handle_unity_errors
def info(target: Optional[str], search_method: Optional[str]):
    """Get AudioSource info for a target, or list all if no target given.

    \b
    Examples:
        unity-mcp audio info
        unity-mcp audio info "MusicPlayer"
    """
    config = get_config()

    if target:
        params: dict[str, Any] = {
            "action": "get_audio_info",
            "target": target,
        }
        if search_method:
            params["searchMethod"] = search_method
    else:
        params = {"action": "get_audio_info"}

    result = run_command("manage_audio", params, config)
    click.echo(format_output(result, config.format))


@audio.command("mixers")
@handle_unity_errors
def mixers():
    """List all AudioMixer assets in the project.

    \b
    Examples:
        unity-mcp audio mixers
    """
    config = get_config()
    result = run_command("manage_audio", {"action": "find_mixers"}, config)
    click.echo(format_output(result, config.format))


@audio.command("mixer-info")
@click.argument("mixer_path")
@handle_unity_errors
def mixer_info(mixer_path: str):
    """Get info about an AudioMixer (groups, snapshots, exposed parameters).

    \b
    Examples:
        unity-mcp audio mixer-info "Assets/Audio/MainMixer.mixer"
    """
    config = get_config()
    result = run_command("manage_audio", {"action": "get_mixer_info", "mixerPath": mixer_path}, config)
    click.echo(format_output(result, config.format))


@audio.command("set-param")
@click.argument("mixer_path")
@click.argument("param_name")
@click.argument("value", type=float)
@handle_unity_errors
def set_param(mixer_path: str, param_name: str, value: float):
    """Set an exposed float parameter on an AudioMixer.

    \b
    Examples:
        unity-mcp audio set-param "Assets/Audio/MainMixer.mixer" MasterVolume -10.0
    """
    config = get_config()
    params: dict[str, Any] = {
        "action": "set_mixer_float",
        "mixerPath": mixer_path,
        "properties": {"paramName": param_name, "value": value},
    }
    result = run_command("manage_audio", params, config)
    click.echo(format_output(result, config.format))


@audio.command("snapshot")
@click.argument("mixer_path")
@click.argument("snapshot_name")
@click.option("--time", "-t", type=float, default=0.0, help="Transition time in seconds.")
@handle_unity_errors
def snapshot(mixer_path: str, snapshot_name: str, time: float):
    """Transition an AudioMixer to a named snapshot (Play Mode only).

    \b
    Examples:
        unity-mcp audio snapshot "Assets/Audio/MainMixer.mixer" Quiet --time 1.5
    """
    config = get_config()
    params: dict[str, Any] = {
        "action": "transition_to_snapshot",
        "mixerPath": mixer_path,
        "properties": {"snapshotName": snapshot_name, "timeToReach": time},
    }
    result = run_command("manage_audio", params, config)
    click.echo(format_output(result, config.format))


@audio.command("route")
@click.argument("target")
@click.argument("mixer_path")
@click.option("--group", "-g", default="Master", help="Mixer group path (e.g. 'Master/Music').")
@click.option(
    "--search-method",
    type=SEARCH_METHOD_CHOICE_BASIC,
    default=None,
    help="How to find the target.",
)
@handle_unity_errors
def route(target: str, mixer_path: str, group: str, search_method: Optional[str]):
    """Route an AudioSource to a mixer group.

    \b
    Examples:
        unity-mcp audio route "MusicPlayer" "Assets/Audio/MainMixer.mixer" --group "Master/Music"
    """
    config = get_config()
    params: dict[str, Any] = {
        "action": "set_group_output",
        "target": target,
        "mixerPath": mixer_path,
        "properties": {"group": group},
    }
    if search_method:
        params["searchMethod"] = search_method
    result = run_command("manage_audio", params, config)
    click.echo(format_output(result, config.format))
