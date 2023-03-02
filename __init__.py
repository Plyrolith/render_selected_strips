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


def register():
    """
    Main registration.
    """
    # Classes registration
    bpy.utils.register_class(ops.RENDERSELECTEDSTRIPS_OT_RenderSelectedStrips)

    # Add button to strip menu
    bpy.types.SEQUENCER_MT_strip.append(draw.render_selected_strips)


def unregister():
    """
    De-registration.
    """
    # Remove button from strip menu
    bpy.types.SEQUENCER_MT_strip.remove(draw.render_selected_strips)

    # Classes un-registration
    bpy.utils.unregister_class(ops.RENDERSELECTEDSTRIPS_OT_RenderSelectedStrips)
