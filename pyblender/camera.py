import bpy

from .utils import look_at


class Camera:
    def __init__(self,
                 location=(0, 0, 0),
                 rotation=(0, 0, 0),
                 focus_point=None,
                 use_dof=False,
                 aperture_ratio=1,
                 aperture_fstop=2.8,
                 lens=50):
        cam_data = bpy.data.cameras.new('camera')
        # cam_data.dof.focus_distance = focus_distance
        if focus_point is not None:
            from .mesh import Empty
            null = Empty(focus_point)
            cam_data.dof.focus_object = null.obj

        cam_data.dof.aperture_ratio = aperture_ratio
        cam_data.dof.aperture_fstop = aperture_fstop
        # cam_data.dof.aperture_blades = 8
        if use_dof:
            cam_data.dof.use_dof = True
        cam_data.lens = lens

        cam = bpy.data.objects.new('camera', cam_data)
        cam.location = location
        cam.rotation_euler = rotation
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

        for fc in self.obj.animation_data.action.fcurves:
            fc.extrapolation = 'LINEAR'  # Set extrapolation type

        # Iterate over this fcurve's keyframes and set handles to vector
        for kp in fc.keyframe_points:
            kp.handle_left_type = 'VECTOR'
            kp.handle_right_type = 'VECTOR'
