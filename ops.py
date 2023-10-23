from __future__ import annotations
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from bpy.types import Context, Event, ImageSequence

from pathlib import Path

import bpy
from bpy.props import BoolProperty, CollectionProperty, IntProperty, StringProperty
from bpy.types import OperatorFileListElement, Operator
from bpy_extras.io_utils import ImportHelper
from . import utils


OPERATOR_RETURN_ITEMS = set[
    Literal[
        "CANCELLED",
        "FINISHED",
        "INTERFACE",
        "PASS_THROUGH",
        "RUNNING_MODAL",
    ]
]

########################################################################################
# Shared properties
########################################################################################


channel_prop = IntProperty(
    name="Channel",
    description="Add newly created strips to this sequencer channel",
    default=1,
    min=1,
)
directory_prop = StringProperty(name="Directory", subtype="DIR_PATH")
files_prop = CollectionProperty(
    name="File Paths",
    type=OperatorFileListElement,
    options={"HIDDEN", "SKIP_SAVE"},
)
use_fit_prop = BoolProperty(
    name="Fit Scale",
    description="Scale each image to fit the format while preserving aspect ratio",
    default=True,
)


########################################################################################
# Strip import operators
########################################################################################


class RENDERSELECTEDSTRIPS_OT_AddMovieStrips(Operator, ImportHelper):
    """Add multiple videos as a sequence of movie strips to the sequencer"""

    bl_idname = "sequencer.add_movie_strips"
    bl_label = "Add Movie Strips"
    bl_options = {"REGISTER", "UNDO"}

    channel: channel_prop
    directory: directory_prop
    files: files_prop
    filter_glob: StringProperty(
        default=f"*{';*'.join(bpy.path.extensions_movie)}",
        options={"HIDDEN"},
    )
    import_audio: BoolProperty(
        name="Import Audio",
        description="Create audio strips on the next channel if available",
        default=True,
    )
    use_fit: use_fit_prop

    @classmethod
    def poll(cls, context):
        """
        Allow operator to run if the active scene has a sequencer.

        Parameters:
            - context (Context)

        Returns:
            - bool: Whether the active scene has a sequencer or not
        """
        return context.scene.sequence_editor

    def execute(self, context: Context) -> OPERATOR_RETURN_ITEMS:
        """
        Add multiple videos as a sequence of movie strips to the sequencer.

        Parameters:
            - context (Context)

        Returns:
            - set[str]: CANCELLED, FINISHED, INTERFACE, PASS_THROUGH, RUNNING_MODAL
        """
        if TYPE_CHECKING:
            file: OperatorFileListElement
            sequence: ImageSequence

        sequence_editor = context.scene.sequence_editor

        current_frame = context.scene.frame_current
        for file in self.files:
            filepath = Path(self.directory, file.name).resolve()
            if not filepath.is_file():
                continue

            print(f"Adding movie strip: {filepath}")
            sequence = sequence_editor.sequences.new_movie(
                name=filepath.name,
                filepath=filepath.as_posix(),
                channel=self.channel,
                frame_start=current_frame,
                fit_method="FIT" if self.use_fit else "ORIGINAL",
            )
            if self.import_audio:
                sequence_editor.sequences.new_sound(
                    name="audio",
                    filepath=filepath.as_posix(),
                    channel=self.channel + 1,
                    frame_start=current_frame,
                )
            current_frame = sequence.frame_final_end

        return {"FINISHED"}


class RENDERSELECTEDSTRIPS_OT_AddStillStrips(Operator, ImportHelper):
    """Add multiple images as still image strips to the sequencer"""

    bl_idname = "sequencer.add_still_strips"
    bl_label = "Add Still Strips"
    bl_options = {"REGISTER", "UNDO"}

    channel: channel_prop
    directory: directory_prop
    duration: IntProperty(
        name="Frame Duration",
        description="Length of each created image strip",
        default=24,
        min=1,
    )
    files: files_prop
    filter_glob: StringProperty(
        default=f"*{';*'.join(bpy.path.extensions_image)}",
        options={"HIDDEN"},
    )
    use_fit: use_fit_prop

    @classmethod
    def poll(cls, context) -> bool:
        """
        Allow operator to run if the active scene has a sequencer.

        Parameters:
            - context (Context)

        Returns:
            - bool: Whether the active scene has a sequencer or not
        """
        return context.scene.sequence_editor

    def execute(self, context: Context) -> OPERATOR_RETURN_ITEMS:
        """
        Add multiple images as a sequence of image strips to the sequencer.

        Parameters:
            - context (Context)

        Returns:
            - set[str]: CANCELLED, FINISHED, INTERFACE, PASS_THROUGH, RUNNING_MODAL
        """
        if TYPE_CHECKING:
            file: OperatorFileListElement
            sequence: ImageSequence

        sequence_editor = context.scene.sequence_editor

        current_frame = context.scene.frame_current
        for file in self.files:
            filepath = Path(self.directory, file.name).resolve()
            if not filepath.is_file():
                continue

            print(f"Adding as still: {filepath}")
            sequence = sequence_editor.sequences.new_image(
                name=filepath.name,
                filepath=filepath.as_posix(),
                channel=self.channel,
                frame_start=current_frame,
                fit_method="FIT" if self.use_fit else "ORIGINAL",
            )
            sequence.frame_final_duration = self.duration
            current_frame += self.duration

        return {"FINISHED"}


class RENDERSELECTEDSTRIPS_OT_RenderSelectedStrips(Operator):
    """Render selected sequencer strips to a folder"""

    bl_idname = "sequencer.render_selected_strips"
    bl_label = "Render Selected Strips"
    bl_options = {"REGISTER"}

    directory: bpy.props.StringProperty(name="Directory", subtype="DIR_PATH")

    @classmethod
    def poll(cls, context: Context) -> bool:
        """
        Allow operator to run if any strips are selected.

        Parameters:
            - context (Context)

        Returns:
            - bool: Whether strips are selected or not
        """
        if context.area.ui_type != "SEQUENCE_EDITOR":
            return False

        return bool(context.selected_sequences)

    def invoke(self, context: Context, event: Event) -> OPERATOR_RETURN_ITEMS:
        """
        Start folder selection.

        Parameters:
            - context (Context)
            - event (Event)

        Returns:
            - set[str]: CANCELLED, FINISHED, INTERFACE, PASS_THROUGH, RUNNING_MODAL
        """
        context.window_manager.fileselect_add(self)

        return {"RUNNING_MODAL"}

    def execute(self, context: Context) -> OPERATOR_RETURN_ITEMS:
        """
        Back up used scene properties, export sequences and restore backup.

        Parameters:
            - context (Context)

        Returns:
            - set[str]: CANCELLED, FINISHED, INTERFACE, PASS_THROUGH, RUNNING_MODAL
        """
        scene = context.scene

        # Backup
        frame_end_backup = scene.frame_end
        frame_start_backup = scene.frame_start
        filepath_backup = scene.render.filepath

        # Render sequences
        utils.render_sequences(
            sequences=context.selected_sequences,
            directory=self.directory,
        )

        # Restore
        scene.frame_end = frame_end_backup
        scene.frame_start = frame_start_backup
        scene.render.filepath = filepath_backup

        # Report
        self.report(
            {"INFO"},
            f"Finished rendering {len(context.selected_sequences)} strips",
        )

        return {"FINISHED"}
