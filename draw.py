from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bpy.types import Context, Panel

from . import ops


def add_strips(self: Panel, context: Context):
    """
    Draw the operator buttons for adding multiple images and videos.

    Parameters:
        - context (Context)
    """
    layout = self.layout
    layout.separator()
    layout.operator(
        operator=ops.RENDERSELECTEDSTRIPS_OT_AddStillStrips.bl_idname,
        text="Stills",
        icon="RENDERLAYERS",
    )
    layout.operator(
        operator=ops.RENDERSELECTEDSTRIPS_OT_AddMovieStrips.bl_idname,
        text="Movies",
        icon="RENDER_ANIMATION",
    )


def render_selected_strips(self: Panel, context: Context):
    """
    Draw the operator button for the sequence editor strip menu.

    Parameters:
        - context (Context)
    """
    layout = self.layout
    layout.separator()

    layout.operator(
        operator=ops.RENDERSELECTEDSTRIPS_OT_RenderSelectedStrips.bl_idname,
        icon="RENDER_ANIMATION",
    )
