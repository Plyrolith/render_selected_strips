from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Sequence

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


def render_strips(strips: Sequence[Strip], directory: Path | str | None = None):
    """
    Render given sequence stips using their scene's render settings and their names as
    file names.

    Args:
        strips (list[Strip]): Strips to render
        directory (Path | str): Destination folder, scene output if none is given
    """
    if TYPE_CHECKING:
        scene: Scene

    # Generate directory path
    scene = bpy.context.scene
    if directory is None:
        directory = Path(scene.render.filepath).with_suffix("")
    else:
        directory = Path(directory)

    # Loop through sequence strips
    for strip in strips:
        scene = strip.id_data.original  # type: ignore

        # FFMPEG video
        file_format = scene.render.image_settings.file_format
        if file_format == "FFMPEG":
            suffix = FFMPEG_EXTENSIONS_MAP[scene.render.ffmpeg.format]
            filepath = Path(directory, strip.name).with_suffix(suffix)

        # AVI video
        elif file_format in {"AVI_JPEG", "AVI_RAW"}:
            filepath = Path(directory, strip.name).with_suffix(".avi")

        # Image sequences
        else:
            filepath = Path(directory, strip.name, strip.name + "_")

        # Create parent folder
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Set output path
        filepath = filepath.as_posix()
        scene.render.filepath = filepath
        print(f"Rendering {strip.name} to {filepath}")

        # Set scene range
        scene.frame_end = strip.frame_final_end - 1
        scene.frame_start = strip.frame_final_start

        # Render
        scene.render.use_sequencer = True
        bpy.ops.render.render(animation=True, use_viewport=False, scene=scene.name)
