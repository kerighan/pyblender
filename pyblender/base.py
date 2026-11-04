"""Common behaviour for every wrapped Blender object: transforms, keyframes, tweens.

Rotations are given in degrees everywhere in pyblender.
"""

import math

import bpy
import numpy as np

from .animation.easing import EASINGS
from .utils import look_at, to_degrees, to_radians


def link_to_scene(obj):
    """Link ``obj`` to the active collection so it is rendered."""
    bpy.context.collection.objects.link(obj)
    return obj


def deselect_all():
    if bpy.context.object is not None and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")


# transform names → (where, Blender attribute, user→Blender converter, Blender→user converter)
_TRANSFORMS = {
    "location": ("obj", "location", None, None),
    "rotation": ("obj", "rotation_euler", to_radians, to_degrees),
    "scale": ("obj", "scale", None, None),
}


def _as_array(value, like=None):
    """A float array; a scalar is broadcast to the shape of ``like`` when that is a vector."""
    if like is not None and np.ndim(like) == 1 and np.ndim(value) == 0:
        return np.full(len(like), float(value))
    return np.asarray(value, dtype=float)


class Tweenable:
    """Mixin: ``to()``, ``from_()`` and ``wait()`` with a per-object playhead."""

    _cursor = 0
    _last_start = 0

    def _resolve(self, name):
        """Map a tween property name to ``(datablock, attribute, to_blender, to_user)``."""
        raise NotImplementedError

    def _start_frame(self, start):
        if start is None:
            return self._cursor
        if start == "<":
            return self._last_start
        return int(start)

    def _tween(self, props, duration, easing, start, reverse=False):
        start = self._start_frame(start)
        frames = range(start, start + duration + 1)
        progress = np.asarray(EASINGS[easing](np.linspace(0, 1, duration + 1)), dtype=float)
        for name, target in props.items():
            data, attribute, convert, _ = self._resolve(name)
            current = getattr(data, attribute)
            current = _as_array(tuple(current) if hasattr(current, "__len__") else current)
            if convert is not None:
                target = convert(target)
            target = _as_array(target, like=current)
            a, b = (target, current) if reverse else (current, target)
            if a.ndim:
                values = a + (b - a) * progress[:, None]
            else:
                values = a + (b - a) * progress
            self.animate(attribute, values, frames, data=data)
        self._last_start = start
        self._cursor = start + duration
        return self

    def to(self, duration=20, easing="cubic-out", start=None, **props):
        """Tween properties from their current value to the given ones, then advance the
        playhead. ``start``: a frame, ``None`` for the playhead, ``"<"`` to run in parallel
        with the previous tween.

        ::

            cube.to(location=(0, 0, 2), duration=30, easing="back-out")
            cube.to(rotation=(0, 0, 180), scale=0.5, duration=20)      # chained after
            light.to(energy=0, duration=60)                             # any property
        """
        return self._tween(props, duration, easing, start)

    def from_(self, duration=20, easing="cubic-out", start=None, **props):
        """Tween properties from the given values to their current ones (an entrance)."""
        return self._tween(props, duration, easing, start, reverse=True)

    def wait(self, frames):
        """Advance the playhead without animating."""
        self._cursor += int(frames)
        return self

    @property
    def cursor(self):
        """The playhead: the frame where the next tween starts."""
        return self._cursor

    @cursor.setter
    def cursor(self, frame):
        self._cursor = int(frame)


class BlenderObject(Tweenable):
    """Thin wrapper around a ``bpy.types.Object``.

    Subclasses set ``self.obj``. Objects made of several parts (a split text, a
    multi-object model) set ``self.parts`` (a :class:`Group`) and use an empty as ``obj``:
    transforms and keyframes on ``obj`` then move the whole group.
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
        self.obj.scale = value if hasattr(value, "__len__") else (value, value, value)

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
    # Generic access
    # ------------------------------------------------------------------

    @property
    def data(self):
        """The object's datablock (mesh, light, camera…)."""
        return self.obj.data

    def set(self, **properties):
        """Set any property of the wrapper, the object or its datablock:
        ``light.set(energy=10, shadow_soft_size=2)``, ``cube.set(display_type="WIRE")``."""
        for name, value in properties.items():
            if isinstance(getattr(type(self), name, None), property):
                setattr(self, name, value)
            elif hasattr(self.obj, name):
                setattr(self.obj, name, value)
            elif self.data is not None and hasattr(self.data, name):
                setattr(self.data, name, value)
            else:
                raise AttributeError(f"{type(self).__name__} has no property {name!r}")
        return self

    def _resolve(self, name):
        if name in _TRANSFORMS:
            where, attribute, convert, back = _TRANSFORMS[name]
            return self.obj, attribute, convert, back
        if hasattr(self.obj, name) and not isinstance(getattr(type(self), name, None), property):
            return self.obj, name, None, None
        if self.data is not None and hasattr(self.data, name):
            return self.data, name, None, None
        raise AttributeError(f"{type(self).__name__} has no animatable property {name!r}")

    # ------------------------------------------------------------------
    # Visibility and selection
    # ------------------------------------------------------------------

    def set_visible(self, visible=True):
        self.obj.hide_viewport = not visible
        self.obj.hide_render = not visible
        return self

    def hide_until(self, frame):
        """Keep the object hidden before ``frame``."""
        return self.animate_visibility([False, True], [frame - 1, frame])

    def hide_from(self, frame):
        """Hide the object from ``frame`` on."""
        return self.animate_visibility([True, False], [frame, frame + 1])

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
    # Keyframes (the low-level layer under ``to()`` / ``from_()``)
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
        """Keyframe render and viewport visibility from booleans (True = visible)."""
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


class Group(Tweenable):
    """A list of objects that behaves like one: every method call is applied to all
    members, tweens accept ``stagger`` and per-member values, and the ready-made
    motions (``pop_in``, ``slide_in``, ``wave``…) live here.

    ::

        cubes = pb.Group(pb.Cube(location=(i, 0, 0)) for i in range(20))
        cubes.from_(scale=0, duration=10, stagger=1, easing="back-out")
        cubes.to(location=lambda i, cube: (i, 0, math.sin(i)), duration=30)
        cubes[5:].set_material("#FF0000")

    A property given as a callable receives ``(index, member)`` and returns the value.
    """

    def __init__(self, members=()):
        self.members = list(members)

    def __iter__(self):
        return iter(self.members)

    def __len__(self):
        return len(self.members)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return Group(self.members[index])
        return self.members[index]

    def __add__(self, other):
        return Group(self.members + list(other))

    def __getattr__(self, name):
        if name.startswith("_") or not self.members:
            raise AttributeError(name)
        attribute = getattr(self.members[0], name)
        if not callable(attribute):
            return [getattr(member, name) for member in self.members]

        def call(*args, **kwargs):
            results = [getattr(member, name)(*args, **kwargs) for member in self.members]
            if all(r is m for r, m in zip(results, self.members)):
                return self
            return results
        return call

    # ------------------------------------------------------------------
    # Staggered tweens
    # ------------------------------------------------------------------

    def _ordered(self, reverse):
        members = list(enumerate(self.members))
        return members[::-1] if reverse else members

    def _group_tween(self, method, props, duration, easing, start, stagger, reverse):
        start = self._start_frame(start)
        for order, (index, member) in enumerate(self._ordered(reverse)):
            values = {k: v(index, member) if callable(v) else v for k, v in props.items()}
            getattr(member, method)(duration=duration, easing=easing,
                                    start=start + order * stagger, **values)
        self._last_start = start
        self._cursor = start + duration + stagger * max(len(self.members) - 1, 0)
        return self

    def to(self, duration=20, easing="cubic-out", start=None, stagger=0, reverse=False, **props):
        """Tween every member, each one delayed by ``stagger`` frames from the previous."""
        return self._group_tween("to", props, duration, easing, start, stagger, reverse)

    def from_(self, duration=20, easing="cubic-out", start=None, stagger=0, reverse=False,
              **props):
        return self._group_tween("from_", props, duration, easing, start, stagger, reverse)

    def _each_frames(self, start, duration, stagger, reverse):
        """Yield ``(index, member, first_frame)`` for staggered motions."""
        start = self._start_frame(start)
        for order, (index, member) in enumerate(self._ordered(reverse)):
            yield index, member, start + order * stagger
        self._last_start = start
        self._cursor = start + duration + stagger * max(len(self.members) - 1, 0)

    # ------------------------------------------------------------------
    # Motions
    # ------------------------------------------------------------------

    def pop_in(self, duration=15, stagger=2, easing="back-out", start=None, scale_from=0.0,
               reverse=False):
        """Scale each part up from ``scale_from``. Parts are invisible before."""
        return self.from_(duration, easing, start, stagger, reverse,
                          scale=lambda i, m: np.array(m.obj.scale) * scale_from)

    def pop_out(self, duration=15, stagger=2, easing="back-in", start=None, scale_to=0.0,
                reverse=False):
        """Scale each part down to ``scale_to``, then hide it."""
        for index, member, first in self._each_frames(start, duration, stagger, reverse):
            member.to(duration, easing, first, scale=np.array(member.obj.scale) * scale_to)
            member.hide_from(first + duration)
        return self

    def slide_in(self, offset=(0, -1, 0), duration=20, stagger=2, easing="cubic-out", start=None,
                 reverse=False):
        """Move each part from ``current + offset`` to its place. Parts are hidden before.

        For an upright text the local Y axis points up: ``offset=(0, -1, 0)`` rises from below.
        """
        offset = np.asarray(offset, dtype=float)
        for index, member, first in self._each_frames(start, duration, stagger, reverse):
            member.from_(duration, easing, first, location=np.array(member.obj.location) + offset)
            member.hide_until(first)
        return self

    def slide_out(self, offset=(0, 1, 0), duration=20, stagger=2, easing="cubic-in", start=None,
                  reverse=False):
        """Move each part by ``offset``, then hide it."""
        offset = np.asarray(offset, dtype=float)
        for index, member, first in self._each_frames(start, duration, stagger, reverse):
            member.to(duration, easing, first, location=np.array(member.obj.location) + offset)
            member.hide_from(first + duration)
        return self

    def flip_in(self, angle=(90, 0, 0), duration=20, stagger=2, easing="back-out", start=None,
                reverse=False):
        """Rotate each part from ``current + angle`` (degrees) to its place. Hidden before."""
        angle = np.asarray(angle, dtype=float)
        for index, member, first in self._each_frames(start, duration, stagger, reverse):
            member.from_(duration, easing, first, rotation=np.array(member.rotation) + angle)
            member.hide_until(first)
        return self

    def flip_out(self, angle=(-90, 0, 0), duration=20, stagger=2, easing="back-in", start=None,
                 reverse=False):
        """Rotate each part by ``angle`` (degrees), then hide it."""
        angle = np.asarray(angle, dtype=float)
        for index, member, first in self._each_frames(start, duration, stagger, reverse):
            member.to(duration, easing, first, rotation=np.array(member.rotation) + angle)
            member.hide_from(first + duration)
        return self

    def typewriter(self, stagger=3, start=None, reverse=False):
        """Make parts appear one after the other, without any transition."""
        for index, member, first in self._each_frames(start, 1, stagger, reverse):
            member.hide_until(first)
        return self

    def wave(self, duration=60, amplitude=0.2, period=30, phase=0.6, axis=1, start=None):
        """Oscillate the parts along ``axis`` (0=X, 1=Y, 2=Z, parent space), each one
        lagging the previous by ``phase`` radians. ``period`` is in frames."""
        start = self._start_frame(start)
        frames = range(start, start + duration + 1)
        t = np.arange(len(frames))
        for index, member in enumerate(self.members):
            base = np.array(member.obj.location)
            values = np.repeat(base[None, :], len(frames), axis=0)
            values[:, axis] += amplitude * np.sin(2 * np.pi * t / period - index * phase)
            member.animate_location(values, frames)
            member._cursor = start + duration
        self._last_start, self._cursor = start, start + duration
        return self

    def shake(self, duration=30, amplitude=0.05, seed=0, start=None):
        """Random jitter of each part's location, decaying to rest."""
        rng = np.random.default_rng(seed)
        start = self._start_frame(start)
        frames = range(start, start + duration + 1)
        decay = np.linspace(1, 0, len(frames))
        for member in self.members:
            base = np.array(member.obj.location)
            jitter = rng.uniform(-1, 1, (len(frames), 3)) * amplitude * decay[:, None]
            jitter[-1] = 0
            member.animate_location(base[None, :] + jitter, frames)
            member._cursor = start + duration
        self._last_start, self._cursor = start, start + duration
        return self
