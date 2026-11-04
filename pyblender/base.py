"""Common behaviour for every wrapped Blender object.

Rotations are given in degrees everywhere in pyblender.
"""

import math

import bpy

from .utils import look_at, to_degrees, to_radians


def link_to_scene(obj):
    """Link ``obj`` to the active collection so it is rendered."""
    bpy.context.collection.objects.link(obj)
    return obj


def deselect_all():
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")


class BlenderObject:
    """Thin wrapper around a ``bpy.types.Object``.

    Subclasses set ``self.obj``. Objects made of several parts (a split text, a
    multi-object model) set ``self.parts`` and use an empty as ``obj``: transforms
    and keyframes on ``obj`` then move the whole group.
    """

    obj = None
    parts = ()

    # ------------------------------------------------------------------
    # Transforms
    # ------------------------------------------------------------------

    @property
    def location(self):
        return self.obj.location

    @location.setter
    def location(self, value):
        self.obj.location = value

    @property
    def rotation(self):
        """Euler rotation in degrees."""
        return to_degrees(tuple(self.obj.rotation_euler))

    @rotation.setter
    def rotation(self, value):
        self.obj.rotation_euler = to_radians(value)

    @property
    def scale(self):
        return self.obj.scale

    @scale.setter
    def scale(self, value):
        self.obj.scale = value

    def translate(self, x=0.0, y=0.0, z=0.0):
        """Move by an offset."""
        a, b, c = self.obj.location
        self.obj.location = (a + x, b + y, c + z)
        return self

    def rotate(self, x=0.0, y=0.0, z=0.0):
        """Rotate around the world axes (the parent's axes for a parented object) by angles
        in degrees, on top of the current rotation."""
        from mathutils import Euler

        matrix = Euler(to_radians((x, y, z))).to_matrix().to_4x4()
        self.obj.matrix_basis = matrix @ self.obj.matrix_basis
        return self

    def resize(self, factor):
        """Multiply the scale by ``factor`` (a number or a per-axis triple)."""
        if isinstance(factor, (int, float)):
            factor = (factor, factor, factor)
        self.obj.scale = [s * f for s, f in zip(self.obj.scale, factor)]
        return self

    def set_parent(self, parent):
        self.obj.parent = parent.obj if isinstance(parent, BlenderObject) else parent
        return self

    # ------------------------------------------------------------------
    # Visibility and selection
    # ------------------------------------------------------------------

    def set_visible(self, visible=True):
        self.obj.hide_viewport = not visible
        self.obj.hide_render = not visible
        return self

    def set_ray_visibility(self, camera=True, diffuse=True, glossy=True, transmission=True,
                           volume_scatter=True, shadow=True):
        """Cycles ray visibility: hide from the camera but keep reflections, and so on."""
        obj = self.obj
        obj.visible_camera = camera
        obj.visible_diffuse = diffuse
        obj.visible_glossy = glossy
        obj.visible_transmission = transmission
        obj.visible_volume_scatter = volume_scatter
        obj.visible_shadow = shadow
        return self

    set_cycles_visibility = set_ray_visibility

    def select(self, only=True):
        """Select the object (and its parts) and make it active, for ``bpy.ops`` calls."""
        if only:
            deselect_all()
        for part in self.parts or (self,):
            part.obj.select_set(True)
        bpy.context.view_layer.objects.active = self.obj
        return self

    def look_at(self, target):
        """Orient the object towards a point ``(x, y, z)`` or another wrapped object.

        Pointing at an object adds a ``TRACK_TO`` constraint, so the orientation
        follows the target when it is animated.
        """
        if isinstance(target, BlenderObject):
            constraint = self.obj.constraints.new(type="TRACK_TO")
            constraint.target = target.obj
        else:
            look_at(self.obj, target)
        return self

    # ------------------------------------------------------------------
    # Keyframes
    # ------------------------------------------------------------------

    def animate(self, attribute, values, frames=None, data=None, index=-1):
        """Insert one keyframe per value on ``attribute``.

        Arguments:
            attribute: RNA path of the property (``"location"``, ``"energy"``…).
            values: list of values, one per frame.
            frames: frame numbers matching ``values``. Defaults to ``0..len(values)-1``.
            data: the Blender datablock holding the property. Defaults to the object.
            index: component index for vector properties (``-1`` keys all components).
        """
        if frames is None:
            frames = range(len(values))
        data = self.obj if data is None else data
        for frame, value in zip(frames, values):
            setattr(data, attribute, value)
            data.keyframe_insert(attribute, index=index, frame=frame)
        return self

    def animate_location(self, values, frames=None):
        return self.animate("location", values, frames)

    def animate_rotation(self, values, frames=None):
        """Euler angles in degrees, one ``(x, y, z)`` per frame."""
        return self.animate("rotation_euler", [to_radians(v) for v in values], frames)

    def animate_rotation_z(self, values, frames=None):
        """Animate the rotation around Z only, from a list of angles in degrees."""
        if frames is None:
            frames = range(len(values))
        for frame, angle in zip(frames, values):
            self.obj.rotation_euler[2] = math.radians(angle)
            self.obj.keyframe_insert("rotation_euler", index=2, frame=frame)
        return self

    def animate_scale(self, values, frames=None):
        return self.animate("scale", values, frames)

    def animate_scale_z(self, values, frames=None):
        """Animate the scale along Z only, from a list of factors."""
        if frames is None:
            frames = range(len(values))
        for frame, factor in zip(frames, values):
            self.obj.scale[2] = factor
            self.obj.keyframe_insert("scale", index=2, frame=frame)
        return self

    def animate_visibility(self, values, frames=None):
        """Keyframe render and viewport visibility from booleans."""
        for attribute in ("hide_render", "hide_viewport"):
            self.animate(attribute, [not v for v in values], frames)
        return self

    def _fcurves(self):
        for part in self.parts or (self,):
            data = part.obj.animation_data
            if data is not None and data.action is not None:
                yield from data.action.fcurves

    def set_interpolation(self, interpolation="LINEAR", extrapolation=None):
        """Change the interpolation of every keyframe (``LINEAR``, ``BEZIER``, ``CONSTANT``)
        and optionally the extrapolation (``CONSTANT`` or ``LINEAR``)."""
        for fcurve in self._fcurves():
            for point in fcurve.keyframe_points:
                point.interpolation = interpolation
            if extrapolation is not None:
                fcurve.extrapolation = extrapolation
        return self

    def repeat_animation(self, count=0):
        """Loop the animation after its last keyframe, ``count`` times (0 = forever)."""
        for fcurve in self._fcurves():
            modifier = fcurve.modifiers.new(type="CYCLES")
            modifier.cycles_after = count
        return self


class Empty(BlenderObject):
    """An invisible object, handy as a focus or tracking target and to group objects."""

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1), name="empty"):
        self.obj = link_to_scene(bpy.data.objects.new(name, None))
        self.obj.location = location
        self.obj.rotation_euler = to_radians(rotation)
        self.obj.scale = scale
