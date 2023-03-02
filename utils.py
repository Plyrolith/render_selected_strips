from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bpy.types import Scene, Sequence

import bpy
from pathlib import Path


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


def render_sequences(sequences: list[Sequence], directory: Path | str | None = None):
    """
    Render given sequence stips using their scene's render settings and their names as
    file names.

    Parameters:
        - sequences (list[Sequence]): Sequences to render
        - directory (Path | str): Destination folder, use current scene output if none
          is given
    """
    if TYPE_CHECKING:
        scene: Scene

    # Generate directory path
    if directory is None:
        directory = Path(bpy.context.scene.render.filepath).with_suffix("")
    else:
        directory = Path(directory)

    # Loop through sequence strips
    for sequence in sequences:
        scene = sequence.id_data.original

        # FFMPEG video
        file_format = scene.render.image_settings.file_format
        if file_format == "FFMPEG":
            suffix = FFMPEG_EXTENSIONS_MAP[scene.render.ffmpeg.format]
            filepath = Path(directory, sequence.name).with_suffix(suffix)

        # AVI video
        elif file_format in {"AVI_JPEG", "AVI_RAW"}:
            filepath = Path(directory, sequence.name).with_suffix(".avi")

        # Image sequences
        else:
            filepath = Path(directory, sequence.name, sequence.name + "_")

        # Create parent folder
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Set output path
        filepath = filepath.as_posix()
        scene.render.filepath = filepath
        print(f"Rendering {sequence.name} to {filepath}")

        # Set scene range
        scene.frame_end = sequence.frame_final_end - 1
        scene.frame_start = sequence.frame_final_start

        # Render
        scene.render.use_sequencer = True
        bpy.ops.render.render(animation=True, use_viewport=False, scene=scene.name)
