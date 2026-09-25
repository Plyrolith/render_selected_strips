from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from bpy.stub_internal.rna_enums import OperatorReturnItems
    from bpy.types import Area, Context, Event, Preferences, Scene, WindowManager

from pathlib import Path

import bpy
from bpy.props import BoolProperty, CollectionProperty, IntProperty, StringProperty
from bpy.types import Operator, OperatorFileListElement, Strip, Timer
from bpy_extras.io_utils import ImportHelper

from . import utils

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
use_adjust_range = BoolProperty(
    name="Adjust Range",
    description="Set the scene range to the newly created strips",
    default=True,
)


class RENDERSELECTEDSTRIPS_OT_AddMovieStrips(Operator, ImportHelper):
    """Add multiple videos as a sequence of movie strips to the sequencer"""

    bl_idname = "sequencer.add_movie_strips"
    bl_label = "Add Movie Strips"
    bl_options = {"REGISTER", "UNDO"}

    channel: channel_prop
    directory: directory_prop
    files: files_prop
    filter_glob: StringProperty(
        default=f"*{';*'.join(bpy.path.extensions_movie)}",  # type: ignore
        options={"HIDDEN"},
    )
    import_audio: BoolProperty(
        name="Import Audio",
        description="Create audio strips on the next channel if available",
        default=True,
    )
    use_fit: use_fit_prop
    use_adjust_range: use_adjust_range

    @classmethod
    def poll(cls, context) -> bool:
        """
        Allow operator to run if the active scene has a sequencer.

        Args:
            context (Context)

        Returns:
            bool: Whether the active scene has a sequencer or not
        """
        if TYPE_CHECKING:
            scene: Scene

        scene = context.scene
        return bool(scene.sequence_editor)

    def execute(self, context: Context) -> set[OperatorReturnItems]:
        """
        Add multiple videos as a sequence of movie strips to the sequencer.

        Args:
            context (Context)

        Returns:
            set[OperatorReturnItems]
        """
        if TYPE_CHECKING:
            file: OperatorFileListElement
            scene: Scene
            strip: Strip

        scene = context.scene
        sequence_editor = scene.sequence_editor

        current_frame = scene.frame_current
        for file in self.files:
            filepath = Path(self.directory, file.name).resolve()
            if not filepath.is_file():
                continue

            print(f"Adding movie strip: {filepath}")
            strip = sequence_editor.strips.new_movie(
                name=filepath.name,
                filepath=filepath.as_posix(),
                channel=self.channel,
                frame_start=current_frame,
                fit_method="FIT" if self.use_fit else "ORIGINAL",
            )
            if self.import_audio:
                sequence_editor.strips.new_sound(
                    name="audio",
                    filepath=filepath.as_posix(),
                    channel=self.channel + 1,
                    frame_start=current_frame,
                )
            current_frame = strip.frame_final_end

        if self.use_adjust_range:
            scene.frame_start = scene.frame_current
            scene.frame_end = current_frame

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
        default=f"*{';*'.join(bpy.path.extensions_image)}",  # type: ignore
        options={"HIDDEN"},
    )
    use_fit: use_fit_prop
    use_adjust_range: use_adjust_range

    @classmethod
    def poll(cls, context) -> bool:
        """
        Allow operator to run if the active scene has a sequencer.

        Args:
            context (Context)

        Returns:
            bool: Whether the active scene has a sequencer or not
        """
        if TYPE_CHECKING:
            scene: Scene

        scene = context.scene
        return bool(scene.sequence_editor)

    def execute(self, context: Context) -> set[OperatorReturnItems]:
        """
        Add multiple images as a sequence of image strips to the sequencer.

        Args:
            context (Context)

        Returns:
            set[OperatorReturnItems]
        """
        if TYPE_CHECKING:
            file: OperatorFileListElement
            scene: Scene
            strip: Strip

        scene = context.scene
        sequence_editor = scene.sequence_editor

        current_frame = scene.frame_current
        for file in self.files:
            filepath = Path(self.directory, file.name).resolve()
            if not filepath.is_file():
                continue

            print(f"Adding as still: {filepath}")
            strip = sequence_editor.strips.new_image(
                name=filepath.name,
                filepath=filepath.as_posix(),
                channel=self.channel,
                frame_start=current_frame,
                fit_method="FIT" if self.use_fit else "ORIGINAL",
            )
            strip.frame_final_duration = self.duration
            current_frame += self.duration

        if self.use_adjust_range:
            scene.frame_start = scene.frame_current
            scene.frame_end = current_frame

        return {"FINISHED"}


class RENDERSELECTEDSTRIPS_OT_RenderSelectedStrips(Operator):
    """Render selected sequencer strips to a folder"""

    bl_idname = "sequencer.render_selected_strips"
    bl_label = "Render Selected Strips"
    bl_options = {"REGISTER"}

    directory: StringProperty(name="Directory", subtype="DIR_PATH")

    _filepath: str
    _frame_current: int
    _is_cancelled: bool = False
    _is_modal: bool = False
    _is_rendering: bool = False
    _nb_strips: int
    _render_display_type: Literal["NONE", "SCREEN", "AREA", "WINDOW"] = "WINDOW"
    _strips: list[Strip]
    _timer: Timer | None = None

    def _render_cancel_handler(self, scene: Scene, _=None):
        """
        Mark if rendering was cancelled.
        """
        self._is_cancelled = True
        self._is_rendering = False

    def _render_complete_handler(self, scene: Scene, _=None):
        """
        Mark if rendering has completed.
        """
        self._is_rendering = False

    @classmethod
    def poll(cls, context: Context) -> bool:
        """
        Allow operator to run if any strips are selected.

        Args:
            context (Context)

        Returns:
            bool: Whether strips are selected or not
        """
        if TYPE_CHECKING:
            area: Area

        area = context.area
        if area.ui_type != "SEQUENCE_EDITOR":
            return False

        return bool(context.selected_strips)

    def invoke(self, context: Context, event: Event) -> set[OperatorReturnItems]:
        """
        Start folder selection, store render display type and mark modal execution.

        Args:
            context (Context)
            event (Event)

        Returns:
            set[OperatorReturnItems]
        """
        if TYPE_CHECKING:
            prefs: Preferences
            wm: WindowManager

        prefs = context.preferences
        self._render_display_type = prefs.view.render_display_type
        self._is_modal = True

        wm = context.window_manager
        wm.fileselect_add(self)

        return {"RUNNING_MODAL"}

    def render_next_strip(self, context: Context):
        """
        Start rendering the next strip and remove it from the queue.

        Args:
            context (Context)
        """
        if TYPE_CHECKING:
            scene: Scene

        strip = self._strips.pop(0)

        # Report new render task
        nb = self._nb_strips - len(self._strips)
        self.report({"INFO"}, f"Rendering strip {nb}/{self._nb_strips}: {strip.name}")

        # Set scene frame to avoid jumping between renders
        scene = context.scene
        scene.frame_current = strip.frame_final_start

        # Start modal render
        self._is_rendering = True
        utils.render_strip(strip, self.directory, modal=True)

    def modal(self, context: Context, event: Event) -> set[OperatorReturnItems]:
        """
        Handle modal events: Cancelled, rendering, next strip & finished.

        Args:
            context (Context)
            event (Event)

        Returns:
            set[OperatorReturnItems]
        """
        # Has been cancelled
        if self._is_cancelled:
            self.finish(context)
            self.report({"WARNING"}, "Cancelled rendering strips")
            return {"CANCELLED"}

        # Check if current render is still running
        elif self._is_rendering:
            return {"RUNNING_MODAL"}

        # Start rendering next strip
        elif self._strips:
            self.render_next_strip(context)
            return {"RUNNING_MODAL"}

        # Render complete
        self.finish(context)
        self.report({"INFO"}, f"Finished rendering {self._nb_strips} strips")
        return {"FINISHED"}

    def execute(self, context: Context) -> set[OperatorReturnItems]:
        """
        Back up used scene properties, export sequences and restore backup.

        Args:
            context (Context)

        Returns:
            set[OperatorReturnItems]
        """
        if TYPE_CHECKING:
            prefs: Preferences
            scene: Scene
            wm: WindowManager

        # Check strips
        if context.selected_strips:
            strips = list(context.selected_strips)
            strips.sort(key=lambda s: s.frame_start)
        else:
            self.report({"ERROR"}, "No strips selected")
            return {"FINISHED"}

        # Backup scene values
        scene = context.scene
        self._frame_current = scene.frame_current
        self._filepath = scene.render.filepath

        # If not invoked as modal, render directly and finish
        if not self._is_modal:
            for strip in strips:
                utils.render_strip(strip, self.directory, modal=False)
                scene.render.filepath = self._filepath
                scene.frame_current = self._frame_current
            return {"FINISHED"}

        # Keep UI when rendering
        prefs = context.preferences
        prefs.view.render_display_type = "NONE"

        # Add render handlers
        if self._render_cancel_handler not in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.append(self._render_cancel_handler)
        if self._render_complete_handler not in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.append(self._render_complete_handler)

        # Add modal handler
        wm = context.window_manager
        wm.modal_handler_add(self)

        # Add timer
        self._timer = wm.event_timer_add(0.1)

        # Queue strips and start rendering first one
        self._strips = list(strips)
        self._nb_strips = len(strips)
        self.render_next_strip(context)

        return {"RUNNING_MODAL"}

    def finish(self, context: Context):
        """
        Remove timer and render handlers, restore backups.

        Args:
            context (Context)
        """
        if TYPE_CHECKING:
            prefs: Preferences
            scene: Scene
            wm: WindowManager

        self._strips.clear()

        # Remove timer
        if self._timer:
            wm = context.window_manager
            wm.event_timer_remove(self._timer)

        # Remove handlers
        if self._render_cancel_handler in bpy.app.handlers.render_cancel:
            bpy.app.handlers.render_cancel.remove(self._render_cancel_handler)
        if self._render_complete_handler in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.remove(self._render_complete_handler)

        # Restore backed up scene data
        scene = context.scene
        scene.render.filepath = self._filepath
        scene.frame_current = self._frame_current

        # Restore render view settings
        prefs = context.preferences
        prefs.view.render_display_type = self._render_display_type
