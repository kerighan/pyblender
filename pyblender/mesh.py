import bpy

from .utils import look_at


class Mesh:
    def set_material(self, material):
        if material is not None:
            self.obj.data.materials.append(material.mat)

    def set_visible(self, visible):
        if not visible:
            self.obj.hide_viewport = True
            self.obj.hide_render = True

    def init(self, material, visible):
        self.set_material(material)
        self.set_visible(visible)

    def animate_rotation(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        for frame, rotation in zip(frames, values):
            self.obj.rotation_euler = rotation
            self.obj.keyframe_insert("rotation_euler", index=2, frame=frame)

    def animate_rotation_z(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        for frame, rotation in zip(frames, values):
            self.obj.rotation_euler = (0, 0, rotation)
            self.obj.keyframe_insert("rotation_euler", index=2, frame=frame)

    def animate_location(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        for frame, location in zip(frames, values):
            self.obj.location = location
            self.obj.keyframe_insert("location", frame=frame)

    def animate_scale(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        for frame, scale in zip(frames, values):
            self.obj.scale = scale
            self.obj.keyframe_insert("scale", frame=frame)

    def animate_scale_z(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        for frame, scale in zip(frames, values):
            self.obj.scale = (1, 1, scale)
            self.obj.keyframe_insert("scale", frame=frame)

    def animate_color(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        mat = self.obj.data.materials[0]
        bsdf = mat.node_tree.nodes['Principled BSDF']

    def look_at(self, item):
        if isinstance(item, tuple):
            look_at(self.obj, item)
        else:
            constraint = self.obj.constraints.new(type='TRACK_TO')
            constraint.target = item.obj


class Empty(Mesh):
    def __init__(self, location):
        obj = bpy.data.objects.new("empty", None)
        obj.location = location
        self.obj = obj


class Cube(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        size=1,
        material=None,
        visible=True
    ):
        bpy.ops.mesh.primitive_cube_add(
            size=size, location=location, rotation=rotation)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class Sphere(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        radius=1,
        div=8,
        material=None,
        visible=True
    ):
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=radius, location=location, segments=div, ring_count=div)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class IcoSphere(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        radius=1,
        div=8,
        material=None,
        visible=True
    ):
        bpy.ops.mesh.primitive_ico_sphere_add(
            radius=radius, location=location, subdivisions=div)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class Box(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
        size=1,
        material=None,
        visible=True
    ):
        bpy.ops.mesh.primitive_cube_add(
            size=size, location=location,
            scale=scale, rotation=rotation)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class Plane(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
        size=1,
        material=None,
        visible=True
    ):

        bpy.ops.mesh.primitive_plane_add(
            location=location, rotation=rotation, size=size, scale=scale, enter_editmode=True)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class Grid(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(0, 0, 0),
        width=10,
        height=10,
        size=1,
        material=None,
        visible=True
    ):

        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=width, y_subdivisions=height, rotation=rotation, size=size, scale=scale)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class Line(Mesh):
    def __init__(
        self,
        locations,
        stroke_width=0.01,
        material=None,
        visible=True
    ):

        curve_data = bpy.data.curves.new('curve', type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 2
        polyline = curve_data.splines.new("POLY")

        polyline.points.add(len(locations) - 1)
        for i, coord in enumerate(locations):
            x, y, z = coord
            polyline.points[i].co = (x, y, z, 1)

        self.obj = bpy.data.objects.new("curve", curve_data)
        curve_data.bevel_depth = stroke_width
        bpy.context.collection.objects.link(self.obj)

        self.init(material, visible)


class Cylinder(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(0, 0, 0),
        radius=1,
        depth=1,
        div=32,
        material=None,
        visible=True
    ):

        bpy.ops.mesh.primitive_cylinder_add(
            depth=depth, radius=radius,
            location=location, scale=scale,
            rotation=rotation, vertices=div)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class Particles(Mesh):
    def __init__(
            self,
            src, tgt,
            count=500, size=0.2, gravity=1, lifetime=100,
            size_random=0, factor_random=0, angular_velocity_factor=0,
            rotation_factor_random=0, phase_factor_random=0,
            frames=(1, 200), use_dynamic_rotation=True, use_rotations=True,
            lifetime_random=0, time_tweak=1,
            hide_emitter=True):
        src_obj = src.obj
        src_obj.modifiers.new("particles", type='PARTICLE_SYSTEM')

        part = src_obj.particle_systems[0]
        settings = part.settings
        settings.count = count
        settings.emit_from = 'FACE'
        settings.physics_type = 'NEWTON'
        settings.particle_size = size
        settings.render_type = 'OBJECT'
        settings.instance_object = tgt.obj
        settings.lifetime = lifetime
        settings.frame_start = frames[0]
        settings.frame_end = frames[1]
        # settings.show_unborn = True
        # settings.use_dead = True
        settings.angular_velocity_factor = angular_velocity_factor
        settings.phase_factor_random = phase_factor_random
        settings.use_dynamic_rotation = use_dynamic_rotation
        settings.use_rotations = use_rotations
        # settings.brownian_factor = 10
        settings.factor_random = factor_random
        settings.distribution = "JIT"
        settings.lifetime_random = lifetime_random
        settings.time_tweak = time_tweak
        # settings.particle_factor = 1
        settings.size_random = size_random
        # settings.phase_factor = .2
        # settings.radius_scale = .2
        # settings.reactor_factor = .2
        settings.rotation_factor_random = rotation_factor_random
        # bpy.ops.object.duplicates_make_real()
        settings.effector_weights.gravity = gravity

        if hide_emitter:
            src_obj.show_instancer_for_render = False
