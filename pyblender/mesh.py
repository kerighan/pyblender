import bpy

from .base import BlenderObject, link_to_scene


class Mesh(BlenderObject):
    """Base class for meshes and curves. Handles material assignment."""

    def set_material(self, material):
        if material is not None:
            self.obj.data.materials.append(material.mat)
        return self

    def set_smooth(self, smooth=True):
        """Smooth shading: hides the facets of curved surfaces without adding geometry."""
        for polygon in getattr(self.obj.data, "polygons", ()):
            polygon.use_smooth = smooth
        return self

    def _setup(self, material, visible):
        self.set_material(material)
        self.set_visible(visible)

    def _add_primitive(self, operator, material, visible, **kwargs):
        """Run a ``bpy.ops.mesh.primitive_*_add`` operator and wrap the new object."""
        operator(**kwargs)
        self.obj = bpy.context.active_object
        self._setup(material, visible)


class Cube(Mesh):
    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), size=1,
                 material=None, visible=True):
        self._add_primitive(bpy.ops.mesh.primitive_cube_add, material, visible,
                            size=size, location=location, rotation=rotation, scale=scale)


class Plane(Mesh):
    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), size=1,
                 material=None, visible=True):
        self._add_primitive(bpy.ops.mesh.primitive_plane_add, material, visible,
                            size=size, location=location, rotation=rotation, scale=scale)


class Grid(Mesh):
    """A subdivided plane. ``width`` and ``height`` are the number of subdivisions."""

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), size=1,
                 width=10, height=10, material=None, visible=True):
        self._add_primitive(bpy.ops.mesh.primitive_grid_add, material, visible,
                            x_subdivisions=width, y_subdivisions=height,
                            size=size, location=location, rotation=rotation, scale=scale)


class Sphere(Mesh):
    """A UV sphere. ``div`` is the number of segments and rings.

    Spheres are smooth-shaded by default, pass ``smooth=False`` for a faceted look.
    """

    def __init__(self, location=(0, 0, 0), radius=1, div=32, material=None, visible=True,
                 smooth=True):
        self._add_primitive(bpy.ops.mesh.primitive_uv_sphere_add, material, visible,
                            radius=radius, location=location, segments=div, ring_count=div)
        self.set_smooth(smooth)


class IcoSphere(Mesh):
    """An icosphere. ``div`` is the number of subdivisions (keep it below 8)."""

    def __init__(self, location=(0, 0, 0), radius=1, div=3, material=None, visible=True,
                 smooth=True):
        self._add_primitive(bpy.ops.mesh.primitive_ico_sphere_add, material, visible,
                            radius=radius, location=location, subdivisions=div)
        self.set_smooth(smooth)


class Cylinder(Mesh):
    """A cylinder. ``div`` is the number of vertices around the circumference."""

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), radius=1, depth=1,
                 div=32, material=None, visible=True):
        self._add_primitive(bpy.ops.mesh.primitive_cylinder_add, material, visible,
                            radius=radius, depth=depth, vertices=div,
                            location=location, rotation=rotation, scale=scale)


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
