"""Curves: paths that can be rendered as tubes or used as rails for other objects."""

import bpy

from .base import link_to_scene
from .mesh import Mesh
from .utils import to_radians


class Curve(Mesh):
    """Base class: ``stroke_width`` renders the curve as a tube."""

    def _finish(self, stroke_width, material, visible):
        self.obj.data.bevel_depth = stroke_width
        self.obj.data.bevel_resolution = 4
        self._setup(material, visible)

    def follow(self, obj, frames=100, forward="FORWARD_Y"):
        """Make ``obj`` travel along the curve over ``frames`` frames."""
        self.obj.data.use_path = True
        self.obj.data.path_duration = frames
        constraint = obj.obj.constraints.new(type="FOLLOW_PATH")
        constraint.target = self.obj
        constraint.use_curve_follow = True
        constraint.forward_axis = forward
        self.obj.data.animation_data_create()
        self.obj.data.eval_time = 0
        self.obj.data.keyframe_insert("eval_time", frame=0)
        self.obj.data.eval_time = frames
        self.obj.data.keyframe_insert("eval_time", frame=frames)
        return constraint


class BezierCircle(Curve):
    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), radius=1, stroke_width=0.0,
                 material=None, visible=True):
        bpy.ops.curve.primitive_bezier_circle_add(radius=radius, location=location,
                                                  rotation=to_radians(rotation))
        self.obj = bpy.context.active_object
        self._finish(stroke_width, material, visible)


class Bezier(Curve):
    """A smooth curve through ``points`` (NURBS by default, ``kind="BEZIER"`` for handles)."""

    def __init__(self, points, kind="NURBS", resolution=12, cyclic=False, stroke_width=0.0,
                 material=None, visible=True):
        curve = bpy.data.curves.new("curve", type="CURVE")
        curve.dimensions = "3D"
        curve.resolution_u = resolution
        spline = curve.splines.new(kind)
        if kind == "BEZIER":
            spline.bezier_points.add(len(points) - 1)
            for point, (x, y, z) in zip(spline.bezier_points, points):
                point.co = (x, y, z)
                point.handle_left_type = point.handle_right_type = "AUTO"
        else:
            spline.points.add(len(points) - 1)
            for point, (x, y, z) in zip(spline.points, points):
                point.co = (x, y, z, 1)
            spline.use_endpoint_u = True
            spline.order_u = min(4, len(points))
        spline.use_cyclic_u = cyclic
        self.obj = link_to_scene(bpy.data.objects.new("curve", curve))
        self._finish(stroke_width, material, visible)
