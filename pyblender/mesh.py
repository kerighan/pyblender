"""Meshes: primitives, imported models, materials, modifiers and physics."""

import os

import bmesh
import bpy

from .base import BlenderObject, Empty, Group, link_to_scene
from .material import Material, NodeMaterial
from .utils import faces_direction, to_radians


def as_material(material):
    """Accept a material, a color (``"#FF8800"`` or ``(r, g, b)``) or ``None``."""
    if material is None or hasattr(material, "mat"):
        return material
    return Material(color=material)


class Mesh(BlenderObject):
    """Base class for meshes and curves: materials, shading, modifiers, physics.

    Wherever a ``material`` is expected, a color is accepted too and wrapped in a
    :class:`~pyblender.material.Material`.
    """

    # ------------------------------------------------------------------
    # Materials and shading
    # ------------------------------------------------------------------

    def add_material(self, material):
        """Append a material slot."""
        material = as_material(material)
        if material is not None:
            for part in self.parts or (self,):
                part.obj.data.materials.append(material.mat)
        return self

    def set_material(self, material, index=0):
        """Replace the material of slot ``index`` (appends when the slot does not exist)."""
        material = as_material(material)
        if material is None:
            return self
        for part in self.parts or (self,):
            if index < len(part.obj.data.materials):
                part.obj.data.materials[index] = material.mat
            else:
                part.obj.data.materials.append(material.mat)
        return self

    def get_material(self, index=0):
        """Wrap an existing material (by slot index or name) as a :class:`NodeMaterial`."""
        materials = self.obj.data.materials
        if isinstance(index, int):
            return NodeMaterial(material=materials[index])
        for material in materials:
            if material.name == index:
                return NodeMaterial(material=material)
        raise KeyError(f"no material named {index!r}")

    @property
    def material_names(self):
        return [slot.name for slot in self.obj.material_slots]

    def set_smooth(self, smooth=True):
        """Smooth shading: hides the facets of curved surfaces without adding geometry."""
        for part in self.parts or (self,):
            for polygon in getattr(part.obj.data, "polygons", ()):
                polygon.use_smooth = smooth
        return self

    shade_smooth = set_smooth

    def _setup(self, material, visible):
        self.add_material(material)
        self.set_visible(visible)

    def _add_primitive(self, operator, material, visible, rotation=(0, 0, 0), **kwargs):
        """Run a ``bpy.ops.mesh.primitive_*_add`` operator and wrap the new object."""
        operator(rotation=to_radians(rotation), **kwargs)
        self.obj = bpy.context.active_object
        self._setup(material, visible)

    # ------------------------------------------------------------------
    # Mesh editing
    # ------------------------------------------------------------------

    def _edit(self, function):
        """Run ``function(bm)`` on a bmesh of the object and write it back."""
        bm = bmesh.new()
        bm.from_mesh(self.obj.data)
        function(bm)
        bm.to_mesh(self.obj.data)
        bm.free()
        self.obj.data.update()
        return self

    def subdivide(self, cuts=1):
        """Subdivide every edge ``cuts`` times (real geometry, unlike :meth:`add_subdivision`)."""
        return self._edit(lambda bm: bmesh.ops.subdivide_edges(
            bm, edges=bm.edges, cuts=cuts, use_grid_fill=True))

    def remove_faces(self, direction="up", limit=0.5):
        """Delete the faces whose normal points towards ``direction``
        (``"up"``, ``"down"``, ``"front"``, ``"back"``, ``"left"``, ``"right"`` or a vector)."""
        def remove(bm):
            bm.faces.ensure_lookup_table()
            faces = [f for f in bm.faces if faces_direction(f.normal, direction, limit)]
            bmesh.ops.delete(bm, geom=faces, context="FACES_ONLY")
        return self._edit(remove)

    remove_face = remove_faces

    def convert_to_mesh(self):
        """Turn a curve or text into a real mesh (needed before some modifiers)."""
        self.select()
        bpy.ops.object.convert(target="MESH")
        return self

    def apply_modifiers(self):
        self.select()
        bpy.ops.object.convert(target="MESH")
        return self

    # ------------------------------------------------------------------
    # Modifiers (each returns the ``bpy`` modifier for further tweaking)
    # ------------------------------------------------------------------

    def add_modifier(self, kind, name=None, **properties):
        """Add any modifier by Blender type (``"BEVEL"``, ``"SOLIDIFY"``…) and set properties."""
        modifier = self.obj.modifiers.new(name or kind.lower(), kind)
        for key, value in properties.items():
            setattr(modifier, key, value)
        return modifier

    def add_subdivision(self, levels=2, render_levels=None, smooth=True):
        return self.add_modifier("SUBSURF", levels=levels,
                                 render_levels=levels if render_levels is None else render_levels,
                                 subdivision_type="CATMULL_CLARK" if smooth else "SIMPLE")

    def add_displacement(self, texture, strength=1.0, midlevel=0.5, coordinates="LOCAL",
                         direction="NORMAL"):
        """Displace vertices with an image (path, :class:`~pyblender.texture.Image`) or a
        :class:`~pyblender.texture.Texture` / :class:`~pyblender.texture.Noise`."""
        from .texture import Image, Noise, Texture

        if isinstance(texture, (str, Image)):
            texture = Texture(texture)
        datablock = texture.texture if isinstance(texture, (Texture, Noise)) else texture
        return self.add_modifier("DISPLACE", texture=datablock, strength=strength,
                                 mid_level=midlevel, texture_coords=coordinates,
                                 direction=direction)

    def add_boolean(self, other, operation="DIFFERENCE"):
        return self.add_modifier("BOOLEAN", object=other.obj, operation=operation)

    def add_array(self, count=2, offset=(1, 0, 0), relative=True, offset_object=None):
        modifier = self.add_modifier("ARRAY", count=count)
        modifier.use_relative_offset = relative
        modifier.use_constant_offset = not relative
        if relative:
            modifier.relative_offset_displace = offset
        else:
            modifier.constant_offset_displace = offset
        if offset_object is not None:
            modifier.use_object_offset = True
            modifier.offset_object = offset_object.obj
        return modifier

    def add_mirror(self, axis=(True, False, False), mirror_object=None):
        modifier = self.add_modifier("MIRROR", use_axis=axis)
        if mirror_object is not None:
            modifier.mirror_object = mirror_object.obj
        return modifier

    def add_wireframe(self, thickness=0.02, replace=True):
        return self.add_modifier("WIREFRAME", thickness=thickness, use_replace=replace)

    def add_bevel(self, width=0.05, segments=3):
        return self.add_modifier("BEVEL", width=width, segments=segments)

    def add_solidify(self, thickness=0.05):
        return self.add_modifier("SOLIDIFY", thickness=thickness)

    def add_decimate(self, ratio=0.5, kind="COLLAPSE"):
        return self.add_modifier("DECIMATE", decimate_type=kind, ratio=ratio)

    def add_remesh(self, mode="VOXEL", voxel_size=0.1, octree_depth=4, smooth=False):
        return self.add_modifier("REMESH", mode=mode, voxel_size=voxel_size,
                                 octree_depth=octree_depth, use_smooth_shade=smooth,
                                 use_remove_disconnected=True)

    def add_smooth(self, factor=0.5, iterations=1):
        return self.add_modifier("SMOOTH", factor=factor, iterations=iterations)

    def add_ocean(self, **properties):
        return self.add_modifier("OCEAN", **properties)

    def add_explode(self, edge_cut=False):
        """Explode with the object's particle system."""
        return self.add_modifier("EXPLODE", use_edge_cut=edge_cut)

    def add_wave(self, height=0.5, width=1.5, speed=0.25):
        return self.add_modifier("WAVE", height=height, width=width, speed=speed)

    def geometry(self, name="geometry"):
        """Add a Geometry Nodes modifier and return its :class:`~pyblender.geometry.Geometry`."""
        from .geometry import Geometry
        return Geometry(self.obj, name=name)

    # ------------------------------------------------------------------
    # Physics
    # ------------------------------------------------------------------

    @staticmethod
    def _rigid_body_world():
        scene = bpy.context.scene
        if scene.rigidbody_world is None:
            bpy.ops.rigidbody.world_add()
        world = scene.rigidbody_world
        world.enabled = True
        if world.collection is None:
            world.collection = bpy.data.collections.new("rigid_bodies")
        return world

    def rigid_body(self, kind="ACTIVE", mass=1.0, friction=0.5, bounciness=0.5, shape="CONVEX_HULL",
                   damping=0.04, kinematic=False):
        """Make the object a rigid body. ``kind``: ``"ACTIVE"`` (falls, collides) or
        ``"PASSIVE"`` (static obstacle). ``shape``: ``"BOX"``, ``"SPHERE"``, ``"CONVEX_HULL"``,
        ``"MESH"``..."""
        world = self._rigid_body_world()
        if self.obj.name not in world.collection.objects:
            world.collection.objects.link(self.obj)
        body = self.obj.rigid_body
        body.type = kind
        body.mass = mass
        body.friction = friction
        body.restitution = bounciness
        body.collision_shape = shape
        body.linear_damping = damping
        body.kinematic = kinematic
        return body

    def throw(self, velocity, frame=0):
        """Give a rigid body an initial velocity: it is driven for a few frames then released."""
        from mathutils import Vector

        body = self.obj.rigid_body
        if body is not None:
            body.kinematic = True
            self.obj.keyframe_insert("rigid_body.kinematic", frame=frame)
            body.kinematic = False
            self.obj.keyframe_insert("rigid_body.kinematic", frame=frame + 4)
        start = Vector(self.obj.location)
        self.animate_location([start, start + Vector(velocity)], [frame, frame + 4])
        self.set_interpolation("LINEAR")
        return self

    def soft_body(self, mass=1.0, bend=5.0, push=0.5, pull=0.5, goal=False):
        modifier = self.add_modifier("SOFT_BODY")
        settings = modifier.settings
        settings.mass = mass
        settings.bend = bend
        settings.push = push
        settings.pull = pull
        settings.use_goal = goal
        return modifier

    def collision(self):
        """Let particles, cloth and soft bodies collide with this object."""
        modifier = self.add_modifier("COLLISION")
        modifier.settings.use = True
        return modifier

    def cloth(self, quality=5, mass=0.3, stiffness=15.0):
        modifier = self.add_modifier("CLOTH")
        settings = modifier.settings
        settings.quality = quality
        settings.mass = mass
        settings.tension_stiffness = stiffness
        return modifier


# ----------------------------------------------------------------------
# Primitives
# ----------------------------------------------------------------------

class Cube(Mesh):
    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), size=1,
                 material=None, visible=True):
        self._add_primitive(bpy.ops.mesh.primitive_cube_add, material, visible, rotation,
                            size=size, location=location, scale=scale)


Box = Cube


class Plane(Mesh):
    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), size=1,
                 material=None, visible=True):
        self._add_primitive(bpy.ops.mesh.primitive_plane_add, material, visible, rotation,
                            size=size, location=location, scale=scale)


class Grid(Mesh):
    """A subdivided plane. ``width`` and ``height`` are the number of subdivisions."""

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), size=1,
                 width=10, height=10, material=None, visible=True):
        self._add_primitive(bpy.ops.mesh.primitive_grid_add, material, visible, rotation,
                            x_subdivisions=width, y_subdivisions=height,
                            size=size, location=location, scale=scale)


class Sphere(Mesh):
    """A UV sphere. ``div`` is the number of segments (rings are half of it).

    Spheres are smooth-shaded by default, pass ``smooth=False`` for a faceted look.
    """

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), radius=1,
                 div=32, material=None, visible=True, smooth=True, segments=None):
        div = div if segments is None else segments
        self._add_primitive(bpy.ops.mesh.primitive_uv_sphere_add, material, visible, rotation,
                            radius=radius, location=location, scale=scale,
                            segments=div, ring_count=max(div // 2, 3))
        self.set_smooth(smooth)


UVSphere = Sphere


class IcoSphere(Mesh):
    """An icosphere. ``div`` is the number of subdivisions (keep it below 8)."""

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), radius=1,
                 div=3, material=None, visible=True, smooth=True, subdivisions=None):
        div = div if subdivisions is None else subdivisions
        self._add_primitive(bpy.ops.mesh.primitive_ico_sphere_add, material, visible, rotation,
                            radius=radius, location=location, scale=scale, subdivisions=div)
        self.set_smooth(smooth)


class Circle(Mesh):
    """A flat circle (mesh). ``fill`` makes it a disc."""

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), radius=1, div=32, fill=False,
                 material=None, visible=True, segments=None):
        div = div if segments is None else segments
        self._add_primitive(bpy.ops.mesh.primitive_circle_add, material, visible, rotation,
                            radius=radius, location=location, vertices=div,
                            fill_type="TRIFAN" if fill else "NOTHING")


class Cylinder(Mesh):
    """A cylinder. ``div`` is the number of vertices around the circumference,
    ``caps`` one of ``"NGON"``, ``"TRIFAN"`` or ``"NOTHING"`` (open tube)."""

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), radius=1,
                 depth=1, div=32, caps="NGON", material=None, visible=True, segments=None):
        div = div if segments is None else segments
        self._add_primitive(bpy.ops.mesh.primitive_cylinder_add, material, visible, rotation,
                            radius=radius, depth=depth, vertices=div, end_fill_type=caps,
                            location=location, scale=scale)


class Cone(Mesh):
    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), radius=1,
                 depth=2, div=32, material=None, visible=True, segments=None):
        div = div if segments is None else segments
        self._add_primitive(bpy.ops.mesh.primitive_cone_add, material, visible, rotation,
                            radius1=radius, depth=depth, vertices=div,
                            location=location, scale=scale)


class Torus(Mesh):
    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), major_radius=1, minor_radius=0.25,
                 div=48, material=None, visible=True, smooth=True):
        self._add_primitive(bpy.ops.mesh.primitive_torus_add, material, visible, rotation,
                            major_radius=major_radius, minor_radius=minor_radius,
                            major_segments=div, minor_segments=max(div // 4, 6),
                            location=location)
        self.set_smooth(smooth)


class Line(Mesh):
    """A polyline through ``points`` rendered as a tube of radius ``stroke_width``."""

    def __init__(self, points, stroke_width=0.01, material=None, visible=True):
        curve = bpy.data.curves.new("curve", type="CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = 2
        curve.bevel_depth = stroke_width

        polyline = curve.splines.new("POLY")
        polyline.points.add(len(points) - 1)
        for point, (x, y, z) in zip(polyline.points, points):
            point.co = (x, y, z, 1)

        self.obj = link_to_scene(bpy.data.objects.new("curve", curve))
        self._setup(material, visible)


# ----------------------------------------------------------------------
# Imported models
# ----------------------------------------------------------------------

class Model(Mesh):
    """A model imported from a ``.glb`` / ``.gltf``, ``.fbx`` or ``.obj`` file.

    A file holding several objects becomes a group: ``model.parts`` lists them and
    ``model.obj`` is an empty parenting them all.
    """

    IMPORTERS = {
        ".glb": lambda path: bpy.ops.import_scene.gltf(filepath=path),
        ".gltf": lambda path: bpy.ops.import_scene.gltf(filepath=path),
        ".fbx": lambda path: bpy.ops.import_scene.fbx(filepath=path),
        ".obj": lambda path: bpy.ops.import_scene.obj(filepath=path),
    }

    def __init__(self, path, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1),
                 material=None, visible=True):
        extension = os.path.splitext(path)[1].lower()
        if extension not in self.IMPORTERS:
            raise ValueError(f"unsupported model format {extension!r}")
        before = set(bpy.data.objects)
        self.IMPORTERS[extension](os.path.abspath(path))
        imported = [obj for obj in bpy.data.objects if obj not in before]
        roots = [obj for obj in imported if obj.parent is None or obj.parent in before]

        if len(roots) == 1:
            self.obj = roots[0]
            self.parts = ()
        else:
            group = Empty(name="model")
            self.obj = group.obj
            for obj in roots:
                obj.parent = group.obj
            self.parts = Group(_wrap(obj) for obj in imported if obj.type == "MESH")

        self.obj.location = location
        self.obj.rotation_euler = to_radians(rotation)
        self.obj.scale = scale
        if material is not None:
            self.set_material(material)
        self.set_visible(visible)

    get_material_names = Mesh.material_names.fget


def _wrap(obj):
    mesh = Mesh()
    mesh.obj = obj
    return mesh


def merge(meshes, name="merged"):
    """Join several meshes into a single new object (the originals are removed)."""
    bm = bmesh.new()
    for mesh in meshes:
        temp = mesh.obj.data.copy()
        temp.transform(mesh.obj.matrix_world)
        bm.from_mesh(temp)
        bpy.data.meshes.remove(temp)
        bpy.data.objects.remove(mesh.obj)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    data = bpy.data.meshes.new(name)
    bm.to_mesh(data)
    bm.free()
    return _wrap(link_to_scene(bpy.data.objects.new(name, data)))
