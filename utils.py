from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bpy.types import Scene, Strip

from pathlib import Path

import bpy

FFMPEG_EXTENSIONS_MAP = {
    "AVI": ".avi",
    "DV": ".dv",
    "FLASH": ".flv",
    "MKV": ".mkv",
    "MPEG1": ".mpg",
    "MPEG2": ".dvd",
    "MPEG4": ".mp4",
    "OGG": ".ogv",
    "QUICKTIME": ".mov",
    "WEBM": ".webm",
}


def render_strip(
    strip: Strip,
    directory: Path | str | None = None,
    modal: bool = False,
):
    """
    Render given sequence stip using its scene's render settings and its name as
    file names.

    Args:
        strip (Strip): Strip to render
        directory (Path | str): Destination folder
        modal (bool): Start render operator in modal mode
    """
    if TYPE_CHECKING:
        scene: Scene

    scene = strip.id_data.original  # type: ignore

    # Generate destination directory path
    if directory:
        dst_dir = Path(directory)
    else:
        dst_dir = Path(scene.render.filepath).with_suffix("")

    # FFMPEG video
    file_format = scene.render.image_settings.file_format
    if file_format == "FFMPEG":
        suffix = FFMPEG_EXTENSIONS_MAP[scene.render.ffmpeg.format]
        filepath = Path(dst_dir, strip.name).with_suffix(suffix)

    # AVI video
    elif file_format in {"AVI_JPEG", "AVI_RAW"}:
        filepath = Path(dst_dir, strip.name).with_suffix(".avi")

    # Image sequences
    else:
        filepath = Path(dst_dir, strip.name, strip.name + "_")

    # Create parent folder
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Set output path
    filepath_str = filepath.as_posix()
    scene.render.filepath = filepath_str
    print(f"Rendering {scene.name} {strip.name} to {filepath_str}")

    # Render
    scene.render.use_sequencer = True
    bpy.ops.render.render(
        "INVOKE_DEFAULT" if modal else "EXEC_DEFAULT",
        animation=True,
        use_viewport=False,
        use_sequencer_scene=True,
        scene=scene.name,
        frame_start=strip.frame_final_start,
        frame_end=strip.frame_final_end - 1,
    )
