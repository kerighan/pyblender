"""Common behaviour for every wrapped Blender object."""

import bpy

from .utils import look_at


def link_to_scene(obj):
    """Link ``obj`` to the active collection so it is rendered."""
    bpy.context.collection.objects.link(obj)
    return obj


class BlenderObject:
    """Thin wrapper around a ``bpy.types.Object``.

    Subclasses must set ``self.obj`` in their constructor.
    """

    obj = None

    @property
    def location(self):
        return self.obj.location

    @location.setter
    def location(self, value):
        self.obj.location = value

    @property
    def rotation(self):
        return self.obj.rotation_euler

    @rotation.setter
    def rotation(self, value):
        self.obj.rotation_euler = value

    @property
    def scale(self):
        return self.obj.scale

    @scale.setter
    def scale(self, value):
        self.obj.scale = value

    def set_visible(self, visible=True):
        self.obj.hide_viewport = not visible
        self.obj.hide_render = not visible
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
    # Keyframe helpers
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
        return self.animate("rotation_euler", values, frames)

    def animate_rotation_z(self, values, frames=None):
        """Animate the rotation around Z only, from a list of angles in radians."""
        if frames is None:
            frames = range(len(values))
        for frame, angle in zip(frames, values):
            self.obj.rotation_euler[2] = angle
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


class Empty(BlenderObject):
    """An invisible object, handy as a focus or tracking target."""

    def __init__(self, location=(0, 0, 0), name="empty"):
        self.obj = link_to_scene(bpy.data.objects.new(name, None))
        self.obj.location = location
