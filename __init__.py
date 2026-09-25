import bpy

from . import draw, ops

classes = (
    ops.RENDERSELECTEDSTRIPS_OT_AddMovieStrips,
    ops.RENDERSELECTEDSTRIPS_OT_AddStillStrips,
    ops.RENDERSELECTEDSTRIPS_OT_RenderSelectedStrips,
)


def register():
    """
    Main registration.
    """
    # Classes registration
    for cls in classes:
        bpy.utils.register_class(cls)

    # Add buttons to add menu
    bpy.types.SEQUENCER_MT_add.append(draw.add_strips)  # type: ignore

    # Add button to view menu
    bpy.types.SEQUENCER_MT_view.append(draw.render_selected_strips)  # type: ignore


def unregister():
    """
    De-registration.
    """
    # Remove button from strip menu
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Remove button from view menu
    bpy.types.SEQUENCER_MT_view.remove(draw.render_selected_strips)  # type: ignore

    # Remove buttons from add menu
    bpy.types.SEQUENCER_MT_add.remove(draw.add_strips)  # type: ignore
