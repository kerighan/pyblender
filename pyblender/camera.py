import bpy

from .base import BlenderObject, Empty, link_to_scene


class Camera(BlenderObject):
    """A perspective camera.

    Arguments:
        location: camera position.
        focus_point: enables depth of field focused on this point ``(x, y, z)``.
        aperture_fstop: f-stop of the lens, smaller means shallower depth of field.
        aperture_ratio: anamorphic ratio of the bokeh.
        aperture_blades: number of blades of the bokeh shape.
        lens: focal length in millimetres.
    """

    def __init__(
        self,
        location=(0, 0, 0),
        focus_point=None,
        aperture_fstop=2.8,
        aperture_ratio=1.0,
        aperture_blades=8,
        lens=50,
    ):
        data = bpy.data.cameras.new("camera")
        data.lens = lens
        data.dof.aperture_fstop = aperture_fstop
        data.dof.aperture_ratio = aperture_ratio
        data.dof.aperture_blades = aperture_blades
        if focus_point is not None:
            data.dof.use_dof = True
            data.dof.focus_object = Empty(focus_point, name="focus").obj

        self.data = data
        self.obj = link_to_scene(bpy.data.objects.new("camera", data))
        self.obj.location = location
