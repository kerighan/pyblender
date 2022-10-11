from math import radians

import bpy
from mathutils import Euler
from pyblender.mesh import Mesh

from .utils import look_at, to_radians


class Camera(Mesh):
    def __init__(self,
                 location=(0, 0, 0),
                 rotation=(0, 0, 0),
                 focus_point=None,
                 use_dof=False,
                 aperture_ratio=1,
                 aperture_fstop=2.8,
                 lens=50):
        rotation = to_radians(rotation)

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
        # print(dir(cam))
        bpy.context.scene.collection.objects.link(cam)
        # self.obj.layers[0] = True

        self.scene = bpy.context.scene.camera = cam

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
    
    def animate_lens(self, values, frames=None):
        if frames is None:
            frames = range(len(values))

        for frame, lens in zip(frames, values):
            self.obj.data.lens = lens
            self.obj.data.keyframe_insert("lens", frame=frame)


    def animate_rotation(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        for frame, rotation in zip(frames, values):
            self.obj.rotation_euler = rotation
            self.obj.keyframe_insert("rotation_euler", frame=frame)

        for fc in self.obj.animation_data.action.fcurves:
            fc.extrapolation = 'LINEAR'  # Set extrapolation type

        # Iterate over this fcurve's keyframes and set handles to vector
        for kp in fc.keyframe_points:
            kp.handle_left_type = 'VECTOR'
            kp.handle_right_type = 'VECTOR'

    # def rotate(self, x, y, z):
    #     # R = Euler(
    #     #     (radians(x), radians(y), radians(z))
    #     # ).to_matrix().to_4x4()
    #     # self.obj.matrix_world = R @ self.obj.matrix_world
    #     # self.select()
    #     self.deselect_all()
    #     self.obj.select_set(True)
    #     bpy.ops.transform.rotate(value=-1,
    #                              constraint_axis=(False, False, True),
    #                              constraint_orientation='LOCAL', 
    #                              mirror=False, proportional='DISABLED',
    #                              proportional_edit_falloff='SMOOTH', 
    #                              proportional_size=1)

    def translate(self, x, y, z):
        a, b, c = self.obj.location
        self.obj.location = (x + a, y + b, z + c)
