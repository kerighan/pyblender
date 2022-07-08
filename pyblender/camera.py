import bpy

from .utils import look_at


class Camera:
    def __init__(self, location,
                 focus_point=None, use_dof=False, aperture_ratio=1,
                 aperture_fstop=2.8):
        cam_data = bpy.data.cameras.new('camera')
        # cam_data.dof.focus_distance = focus_distance
        if focus_point is not None:
            from .mesh import Empty
            null = Empty(focus_point)
            cam_data.dof.focus_object = null.obj

        cam_data.dof.aperture_ratio = aperture_ratio
        cam_data.dof.aperture_fstop = aperture_fstop
        cam_data.dof.aperture_blades = 8
        if use_dof:
            cam_data.dof.use_dof = True

        cam = bpy.data.objects.new('camera', cam_data)
        cam.location = location
        self.obj = cam

    def look_at(self, item):
        if isinstance(item, tuple):
            look_at(self.obj, item)
        else:
            constraint = self.obj.constraints.new(type='TRACK_TO')
            constraint.target = item.obj

    def animate_location(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        for frame, location in zip(frames, values):
            self.obj.location = location
            self.obj.keyframe_insert("location", frame=frame)
