from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bpy.types import Context, Panel

from . import ops


def render_selected_strips(self: Panel, context: Context):
    """
    Draw the operator button for the sequence editor strip menu.
    """
    layout = self.layout
    layout.separator()

    layout.operator(
        operator=ops.RENDERSELECTEDSTRIPS_OT_RenderSelectedStrips.bl_idname,
        icon="RENDER_ANIMATION",
    )
