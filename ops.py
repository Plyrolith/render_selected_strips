from typing import Literal

import bpy
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


class RENDERSELECTEDSTRIPS_OT_RenderSelectedStrips(bpy.types.Operator):
    """Render selected sequencer strips to a folder"""

    bl_idname = "sequencer.render_selected_strips"
    bl_label = "Render Selected Strips"
    bl_options = {"REGISTER"}

    directory: bpy.props.StringProperty(name="Directory", subtype="DIR_PATH")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
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

    def invoke(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
    ) -> OPERATOR_RETURN_ITEMS:
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

    def execute(self, context: bpy.types.Context) -> OPERATOR_RETURN_ITEMS:
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

        return {"FINISHED"}
