from distutils.errors import UnknownFileError
from math import radians

import bmesh
import bpy
from mathutils import Euler, Vector
from mathutils.bvhtree import BVHTree

from .geometry import Geometry
from .material import NodeMaterial
from .utils import look_at, random_string, to_radians


class Mesh:
    def repeat_animation(self, extend):
        if hasattr(self, "parts"):
            for part in self.parts:
                part.repeat_animation(extend)
            return
        if (
            self.obj.animation_data is not None and
            self.obj.animation_data.action is not None
        ):
            for fcurves_f in self.obj.animation_data.action.fcurves:
                new_modifier = fcurves_f.modifiers.new(type='CYCLES')
                new_modifier.cycles_after = extend

    def add_material(self, material):
        if material is not None:
            self.obj.data.materials.append(material.mat)

    def set_material(self, material, index=0):
        try:
            self.obj.data.materials[index] = material.mat
        except IndexError:
            self.add_material(material)
    
    def get_material(self, index=0):
        if isinstance(index, int):
            return NodeMaterial(material=self.obj.data.materials[index])
        for mat in self.obj.data.materials:
            if mat.name == index:
                return NodeMaterial(material=mat)
        raise ValueError

    def set_visible(self, visible):
        if not visible:
            self.obj.hide_viewport = True
            self.obj.hide_render = True

    def set_cycles_visibility(
        self, camera=True, diffuse=True,
        glossy=True, transmission=True, scatter=True, shadow=True
    ):
        self.obj.visible_camera = camera
        self.obj.visible_diffuse = diffuse
        self.obj.visible_glossy = glossy
        self.obj.visible_transmission = transmission
        self.obj.visible_volume_scatter = scatter
        self.obj.visible_shadow = shadow

    def deselect_all(self):
        try:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        except:
            pass
        bpy.ops.object.select_all(action='DESELECT')

    def select(self):
        if hasattr(self, "parts"):
            self.deselect_all()
            for part in self.parts:
                part.obj.select_set(True)
        else:
            self.deselect_all()
            self.obj.select_set(True)

    def convert_to_mesh(self):
        self.select()
        bpy.ops.object.convert(target="MESH")
        return self

    def shade_smooth(self):
        if not hasattr(self, "parts"):
            for f in self.obj.data.polygons:
                f.use_smooth = True
        else:
            for part in self.parts:
                part.shade_smooth()

    def resize(self, x, y, z):
        self.select()
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.transform.resize(value=(x, y, z))
        # self.obj.data.update()

    def init(self, material, visible):
        self.add_material(material)
        self.set_visible(visible)
    
    def modify_boolean(self, mesh):
        m = self.obj.modifiers.new('boolean', 'BOOLEAN')
        m.object = mesh.obj

    def modify_rigid_body(
        self, active="ACTIVE", mass=1, friction=0.5, restitution=0.5,
        mesh_source="BASE", linear_damping=0.04
    ):
        bpy.context.scene.rigidbody_world.collection.objects.link(self.obj)
        self.obj.rigid_body.type = active
        self.obj.rigid_body.mass = mass
        self.obj.rigid_body.friction = friction
        self.obj.rigid_body.restitution = restitution
        self.obj.rigid_body.kinematic = False
        self.obj.rigid_body.mesh_source = mesh_source
        self.obj.rigid_body.linear_damping = linear_damping

    def modify_soft_body(self, mass=1, bend=5, push=.5, pull=.5):
        m = self.obj.modifiers.new('softbody', 'SOFT_BODY')
        m.settings.mass = mass
        m.settings.push = push
        m.settings.pull = pull
        m.settings.bend = bend
        m.settings.use_goal = False
        return m

    def modify_collision(self):
        m = self.obj.modifiers.new('collision', 'COLLISION')
        m.settings.use = True
        return m

    def modify_decimate(self, decimate_type="COLLAPSE"):
        m = self.obj.modifiers.new('decimate', 'DECIMATE')
        m.decimate_type = decimate_type
        m.use_symmetry = True
        return m

    def modify_explode(self, edge_cut=False):
        m = self.obj.modifiers.new('explode', 'EXPLODE')
        m.use_edge_cut = edge_cut

    def modify_array(
            self, count=2, offset_obj=None, offset_displace=(1, 0, 0)):
        m = self.obj.modifiers.new('array', 'ARRAY')
        m.count = count
        if offset_obj is not None:
            m.offset_object = offset_obj.obj
            m.use_object_offset = True
        m.relative_offset_displace = offset_displace

    def modify_geometry(self):
        return Geometry(self.obj)

    def modify_wireframe(self, thickness=.02):
        m = self.obj.modifiers.new('wireframe', 'WIREFRAME')
        m.thickness = thickness
        return m

    def modify_ocean(self):
        m = self.obj.modifiers.new('ocean', 'OCEAN')
        return m

    def modify_subdivide(
        self, levels=1, render_levels=2, quality=3,
        subdivision_type="CATMULL_CLARK"
    ):
        m = self.obj.modifiers.new('subdivide', 'SUBSURF')
        m.levels = levels
        m.render_levels = render_levels
        m.quality = quality
        m.subdivision_type = subdivision_type
        return m

    def modify_displace(
        self, texture=None, strength=1, mid_level=0, texture_coords="UV"
    ):
        m = self.obj.modifiers.new('displace', 'DISPLACE')
        m.strength = strength
        m.mid_level = mid_level
        m.texture_coords = texture_coords
        if texture is not None:
            if isinstance(texture, str):
                from .texture import Texture
                texture = Texture(texture)
            m.texture = texture.texture
        return m

    def modify_mirror(self, object=None, axis=(True, True, True)):
        m = self.obj.modifiers.new('mirror', 'MIRROR')
        m.use_axis = axis
        if object is not None:
            m.mirror_object = object.obj

    def modify_smooth(self):
        m = self.obj.modifiers.new('smooth', 'SMOOTH')

    def modify_remesh(
        self, mode="VOXEL", remove_disconnected=True, octree_depth=4,
        smooth_shade=False
    ):
        m = self.obj.modifiers.new('remesh', 'REMESH')
        m.mode = mode
        m.use_remove_disconnected = remove_disconnected
        m.use_smooth_shade = smooth_shade
        m.octree_depth = octree_depth

    def scale(self, x=1, y=1, z=1):
        if hasattr(self, "parts"):
            for part in self.parts:
                part.scale(x, y, z)
        else:
            self.select()
            bpy.ops.transform.resize(value=(x, y, z))

    def resize(self, scale=1):
        if hasattr(self, "parts"):
            for part in self.parts:
                part.resize(scale)
        else:
            self.select()
            bpy.ops.transform.resize(value=(scale, scale, scale))

    def rotate(self, x, y, z):
        if hasattr(self, "parts"):
            for part in self.parts:
                part.rotate(x, y, z)
        else:
            R = Euler(
                (radians(x), radians(y), radians(z))
            ).to_matrix().to_4x4()
            self.obj.matrix_world = R @ self.obj.matrix_world
        return self

    def translate(self, x, y, z):
        if hasattr(self, "parts"):
            for part in self.parts:
                part.translate(x, y, z)
        else:
            a, b, c = self.obj.location
            self.obj.location = (x + a, y + b, z + c)
        return self

    def throw(self, velocity, frame_start=0):
        pref_edit = bpy.context.preferences.edit
        keyInterp = pref_edit.keyframe_new_interpolation_type
        pref_edit.keyframe_new_interpolation_type = 'LINEAR'

        start_position = self.obj.location
        velocity = Vector(velocity)

        try:
            self.obj.rigid_body.kinematic = True
            self.obj.keyframe_insert(
                'rigid_body.kinematic',
                frame=frame_start)
            self.obj.rigid_body.kinematic = False
            self.obj.keyframe_insert(
                'rigid_body.kinematic',
                frame=frame_start+4)
            self.obj.rigid_body.use_margin
        except:
            pass

        self.obj.location = start_position
        self.obj.keyframe_insert("location", frame=frame_start)
        self.obj.location = start_position + velocity
        self.obj.keyframe_insert("location", frame=frame_start+4)

        pref_edit.keyframe_new_interpolation_type = keyInterp
    
    def animate_visibility(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        for frame, value in zip(frames, values):
            self.obj.hide_render = value
            self.obj.keyframe_insert(data_path="hide_render", frame=frame)

    def animate_rotation(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        if hasattr(self, "parts"):
            for part in self.parts:
                part.animate_rotation(values, frames)
        else:
            self.obj.rotation_mode = 'XYZ'
            for frame, rotation in zip(frames, values):
                self.obj.rotation_euler = to_radians(rotation)
                kf = self.obj.keyframe_insert(
                    "rotation_euler", index=2, frame=frame)

    def animate_rotation_z(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        if hasattr(self, "parts"):
            for part in self.parts:
                part.animate_rotation_z(values, frames)
        else:
            for frame, rotation in zip(frames, values):
                self.obj.rotation_euler = (0, 0, radians(rotation))
                kf = self.obj.keyframe_insert(
                    "rotation_euler", index=2, frame=frame)

    def animate_location(self, values, frames=None):
        if frames is None:
            frames = range(len(values))
        if hasattr(self, "parts"):
            for part in self.parts:
                part.animate_location(values, frames)
        else:
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

    def look_at(self, item):
        if isinstance(item, tuple):
            look_at(self.obj, item)
        else:
            constraint = self.obj.constraints.new(type='TRACK_TO')
            constraint.target = item.obj

    def remove_face(self, direction="up", limit=.5):
        from .utils import (face_back, face_down, face_front, face_left,
                            face_right, face_up)
        if direction == "up":
            func = face_up
        elif direction == "down":
            func = face_down
        elif direction == "left":
            func = face_left
        elif direction == "right":
            func = face_right
        elif direction == "front":
            func = face_front
        elif direction == "back":
            func = face_back

        bpy.context.view_layer.objects.active = self.obj

        previous_mode = self.obj.mode
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bm = bmesh.new()
        bm.from_mesh(self.obj.data)
        bm.faces.ensure_lookup_table()
        faces = [f for f in bm.faces if func(f.normal, limit=limit)]
        bmesh.ops.delete(bm, geom=faces, context='FACES_ONLY')
        bm.to_mesh(self.obj.data)
        self.obj.data.update()
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bmesh.update_edit_mesh(self.obj.data)
        bpy.ops.object.mode_set(mode=previous_mode, toggle=False)

    def subdivide(self, cuts=1):
        bpy.context.view_layer.objects.active = self.obj

        previous_mode = self.obj.mode
        try:
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        except:
            pass
        bm = bmesh.new()
        bm.from_mesh(self.obj.data)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=cuts,
                                  use_grid_fill=True)
        bm.to_mesh(self.obj.data)
        self.obj.data.update()
        try:
            bpy.ops.object.mode_set(mode=previous_mode, toggle=False)
        except:
            pass


class Empty(Mesh):
    def __init__(self,
                 location=(0, 0, 0), scale=(1, 1, 1), rotation=(0, 0, 0)
                 ):
        obj = bpy.data.objects.new("empty", None)
        obj.location = location
        obj.rotation_euler = to_radians(rotation)
        obj.scale = scale
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
        rotation = to_radians(rotation)
        bpy.ops.mesh.primitive_cube_add(
            size=size, location=location, rotation=rotation)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class Sphere(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        radius=1,
        div=8,
        material=None,
        visible=True
    ):
        rotation = to_radians(rotation)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=radius, location=location, rotation=rotation,
            segments=div, ring_count=div)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class IcoSphere(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
        radius=1,
        div=8,
        material=None,
        visible=True
    ):
        rotation = to_radians(rotation)
        bpy.ops.mesh.primitive_ico_sphere_add(
            radius=radius, location=location, rotation=rotation,
            subdivisions=div, scale=scale)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class UVSphere(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
        radius=1,
        div=32,
        material=None,
        visible=True
    ):
        rotation = to_radians(rotation)
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=radius, location=location, rotation=rotation,
            segments=div, ring_count=div//2, scale=scale)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class Circle(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        radius=1,
        div=32,
        material=None,
        fill=False,
        visible=True
    ):
        if fill:
            fill = "TRIFAN"
        else:
            fill = "NOTHING"
        rotation = to_radians(rotation)
        bpy.ops.mesh.primitive_circle_add(
            radius=radius, location=location, rotation=rotation,
            vertices=div, fill_type=fill)
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
        uv_unwrap=False,
        visible=True
    ):
        rotation = to_radians(rotation)
        bpy.ops.mesh.primitive_cube_add(
            size=size, location=location,
            scale=scale, rotation=rotation)
        self.obj = bpy.context.scene.objects[-1]

        if uv_unwrap:
            bpy.context.scene.objects.active = self.obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.reset()
            bm = bmesh.from_edit_mesh(self.obj.data)

            bm.edges.ensure_lookup_table()
            for edge in bm.edges:
                edge.seam = True

            bm.faces.ensure_lookup_table()
            for face in bm.faces:
                face.select_set(False)

            for face in bm.faces:
                face.material_index = 0
                face.select_set(True)
                bmesh.update_edit_mesh(self.obj.data)
                bpy.ops.uv.unwrap()
                face.select_set(False)

            bpy.ops.object.mode_set(mode='OBJECT')
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
        rotation = to_radians(rotation)
        bpy.ops.mesh.primitive_plane_add(
            location=location, rotation=rotation,
            size=size, scale=scale)
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
        rotation = to_radians(rotation)
        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=width, y_subdivisions=height,
            rotation=rotation, size=size, scale=scale, location=location)
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
        scale=(1, 1, 1),
        radius=1,
        depth=1,
        div=32,
        material=None,
        end_fill_type=None,
        visible=True
    ):
        rotation = to_radians(rotation)
        if end_fill_type is not None:
            bpy.ops.mesh.primitive_cylinder_add(
                depth=depth, radius=radius, end_fill_type=end_fill_type,
                location=location, scale=scale,
                rotation=rotation, vertices=div)
        else:
            bpy.ops.mesh.primitive_cylinder_add(
                depth=depth, radius=radius,
                location=location, scale=scale,
                rotation=rotation, vertices=div)
        self.obj = bpy.context.scene.objects[-1]
        self.init(material, visible)


class Particles(Mesh):
    def __init__(
            self,
            src, tgt=None,
            count=500,
            size=0.2,
            gravity=1,
            emit_from="FACE",
            lifetime=100,
            velocity=1,
            size_random=0,
            factor_random=0,
            angular_velocity_factor=0,
            rotation_factor_random=0,
            phase_factor_random=0,
            frames=(1, 200),
            use_dynamic_rotation=True,
            use_rotations=True,
            use_modifier_stack=False,
            lifetime_random=0,
            time_tweak=1,
            hair=False,
            hair_length=0.25,
            hair_step=5,
            root_radius=1.,
            clump_factor=0,
            clump_shape=0,
            effect_hair=0.,
            brownian_factor=0.,
            length_random=0,
            child_type="NONE",
            material=1,
            hide_emitter=True):
        src_obj = src.obj
        src_obj.modifiers.new("particles", type='PARTICLE_SYSTEM')
        part = src_obj.particle_systems[0]
        part.use_hair_dynamics = True

        settings = part.settings
        settings.count = count
        settings.material = material
        settings.emit_from = emit_from
        settings.physics_type = 'NEWTON'
        settings.child_type = child_type
        settings.lifetime = lifetime
        settings.frame_start = frames[0]
        settings.frame_end = frames[1]

        if hair:
            settings.type = "HAIR"
            settings.hair_step = hair_step
            settings.clump_factor = clump_factor
            settings.clump_shape = clump_shape
            settings.hair_length = hair_length
            settings.particle_size = size
            settings.effect_hair = effect_hair
            # settings.bending_random = 1
            settings.effector_weights.gravity = gravity
            settings.root_radius = root_radius
            # settings.use_even_distribution = False
            settings.length_random = length_random
            settings.use_modifier_stack = True
            settings.use_hair_bspline = True
            settings.child_parting_max = 20
            settings.use_advanced_hair = True
            settings.mass = 24
        else:
            settings.particle_size = size
            if tgt is not None:
                settings.render_type = 'OBJECT'
                settings.instance_object = tgt.obj
            # settings.show_unborn = True
            # settings.use_dead = True
            settings.normal_factor = velocity
            settings.use_modifier_stack = use_modifier_stack
            settings.angular_velocity_factor = angular_velocity_factor
            settings.phase_factor_random = phase_factor_random
            settings.use_dynamic_rotation = use_dynamic_rotation
            settings.use_rotations = use_rotations
            settings.brownian_factor = brownian_factor
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


class Text(Mesh):
    def __init__(
        self,
        text,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        align="CENTER",
        size=1,
        extrude=.1,
        material=None,
        font=None,
        visible=True
    ):
        rotation = to_radians(rotation)

        font_curve = bpy.data.curves.new(type="FONT", name="Font Curve")
        font_curve.body = text
        if font is not None:
            font = bpy.data.fonts.load(font)
            font_curve.font = font
        font_curve.size = size
        font_curve.extrude = extrude
        font_curve.align_x = align
        font_curve.align_y = align
        self.obj = bpy.data.objects.new(name="Font Object",
                                        object_data=font_curve)
        self.obj.rotation_mode = "XYZ"
        bpy.context.scene.collection.objects.link(self.obj)

        self.obj.location = location
        self.obj.rotation_euler = rotation

        self.init(material, visible)


class Model(Mesh):
    def __init__(
        self,
        src,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
        material=None,
        visible=True
    ):
        ext = src[-4:]
        n_objects = len(bpy.context.scene.objects)
        if ".glb" == ext:
            bpy.ops.import_scene.gltf(filepath=src)
        elif ".fbx" == ext:
            bpy.ops.import_scene.fbx(filepath=src)
        elif ".obj" == ext:
            bpy.ops.import_scene.obj(filepath=src)
        else:
            raise UnknownFileError(f"{ext} not supported")
        n_objects = len(bpy.context.scene.objects) - n_objects
        if n_objects > 1:
            self.parts = []
            for obj in bpy.context.scene.objects[-n_objects:]:
                mesh = Mesh()
                mesh.obj = obj
                self.parts.append(mesh)
        else:
            self.obj = bpy.context.scene.objects[-1]                
            self.init(material, visible)
    
    # def get_material(self, index=0):
    #     if len(self.obj.material_slots) == 1:
    #         mat = NodeMaterial(material=self.obj.material_slots[0].material)
    #         return mat

    def get_material_names(self):
        res = []
        for mat in self.obj.material_slots:
            res.append(mat.name)
        return res


def deselect_all():
    try:
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    except:
        pass
    bpy.ops.object.select_all(action='DESELECT')


def merge_geometries(boxes):
    # found here:
    # https://blender.stackexchange.com/questions/140673/how-to-combine-multiple-cubes-with-double-faces
    deselect_all()

    bm = bmesh.new()
    for box in boxes:
        o = box.obj
        o.select_set(True)
        bm.from_mesh(o.data)
        bmesh.ops.transform(bm, verts=bm.verts[-8:],
                            matrix=o.matrix_world)
    bpy.ops.object.delete()

    bvhtree = BVHTree().FromBMesh(bm, epsilon=1e-5)
    faces = bm.faces[:]
    remove = []
    while faces:
        f = faces.pop()
        pair = bvhtree.find_nearest_range(f.calc_center_median(), 1e-4)
        if len(pair) > 2:
            remove.extend(p[2] for p in pair)

    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in set(remove)],
                     context="FACES_KEEP_BOUNDARY")
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    me = bpy.data.meshes.new("CubeBoundaryFaces")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("CubeBoundaryFaces", me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    mesh = Mesh()
    mesh.obj = ob
    return mesh
