import bpy

from . import ops


def render_selected_strips(self: bpy.types.Panel, context: bpy.types.Context):
    """
    Draw the operator button for the sequence editor strip menu.
    """
    layout = self.layout
    layout.separator()

    layout.operator(
        operator=ops.RENDERSELECTEDSTRIPS_OT_RenderSelectedStrips.bl_idname,
        icon="RENDER_ANIMATION",
    )
