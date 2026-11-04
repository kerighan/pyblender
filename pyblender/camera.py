import bpy

from .base import BlenderObject, Empty, link_to_scene
from .utils import to_radians


class Camera(BlenderObject):
    """A perspective camera. Creating one makes it the active scene camera.

    Arguments:
        location: camera position.
        rotation: Euler angles in degrees, usually replaced by ``look_at``.
        focus_point: enables depth of field focused on this point ``(x, y, z)``.
        aperture_fstop: f-stop of the lens, smaller means shallower depth of field.
        aperture_ratio: anamorphic ratio of the bokeh.
        aperture_blades: number of blades of the bokeh shape.
        lens: focal length in millimetres.
        clip: ``(start, end)`` clipping distances.
    """

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), focus_point=None,
                 aperture_fstop=2.8, aperture_ratio=1.0, aperture_blades=8, lens=50,
                 clip=(0.1, 1000)):
        data = bpy.data.cameras.new("camera")
        data.lens = lens
        data.clip_start, data.clip_end = clip
        data.dof.aperture_fstop = aperture_fstop
        data.dof.aperture_ratio = aperture_ratio
        data.dof.aperture_blades = aperture_blades
        if focus_point is not None:
            data.dof.use_dof = True
            data.dof.focus_object = Empty(focus_point, name="focus").obj

        self.data = data
        self.obj = link_to_scene(bpy.data.objects.new("camera", data))
        self.obj.location = location
        self.obj.rotation_euler = to_radians(rotation)
        bpy.context.scene.camera = self.obj

    def set_focus(self, target, fstop=None):
        """Enable depth of field focused on a point or an object."""
        self.data.dof.use_dof = True
        if isinstance(target, BlenderObject):
            self.data.dof.focus_object = target.obj
        else:
            self.data.dof.focus_object = Empty(target, name="focus").obj
        if fstop is not None:
            self.data.dof.aperture_fstop = fstop
        return self

    def animate_lens(self, values, frames=None):
        """Keyframe the focal length (zoom)."""
        return self.animate("lens", values, frames, data=self.data)

    def animate_fstop(self, values, frames=None):
        return self.animate("aperture_fstop", values, frames, data=self.data.dof)
