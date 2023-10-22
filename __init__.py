bl_info = {
    "name": "Render Selected Strips",
    "description": "Quickly render selected sequencer strips",
    "author": "Tristan Weis",
    "version": (1, 0, 0),
    "blender": (3, 4, 1),
    "location": "Sequencer",
    "warning": "",
    "doc_url": "https://github.com/Plyrolith/render_selected_strips",
    "tracker_url": "https://github.com/Plyrolith/render_selected_strips/issues",
    "support": "COMMUNITY",
    "category": "Pipeline",
}


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
    bpy.types.SEQUENCER_MT_add.append(draw.add_strips)

    # Add button to strip menu
    bpy.types.SEQUENCER_MT_strip.append(draw.render_selected_strips)


def unregister():
    """
    De-registration.
    """
    # Remove button from strip menu
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    # Remove button from strip menu
    bpy.types.SEQUENCER_MT_strip.remove(draw.render_selected_strips)

    # Remove buttons from add menu
    bpy.types.SEQUENCER_MT_add.remove(draw.add_strips)
