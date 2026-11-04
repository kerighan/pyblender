"""Keyframe timelines with easing, independent from Blender.

A :class:`Timeline` describes how named attributes evolve between keyframes.
Evaluating it at a time ``t`` gives the attribute values, ready to feed into the
``animate_*`` methods of pyblender objects::

    from pyblender.animation import Timeline

    tl = Timeline(0, 30, 60)                 # keyframes, here in frames
    tl.z = [("cubic-in-out", 0, 2), ("cubic-in-out", 2, 0)]
    tl.color = [("linear", "#FF0000", "#0000FF"), ("constant", "#0000FF")]

    tl[15].z        # 1.0
    tl[45].color    # array([0., 0., 1.])

    cube.animate_location([(0, 0, tl[f].z) for f in range(60)])
"""

import copy

import numpy as np

from ..utils import hex_to_rgb
from .easing import EASINGS, tween

__all__ = ["Timeline", "Cycle", "EASINGS", "tween", "linear", "shake", "flicker", "Movement"]

_RESERVED = {"keyframes", "start", "end", "segments", "delay_", "before", "after", "dtype"}


class Attributes(dict):
    """A dict whose keys are also readable as attributes."""

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        self[name] = value


def _parse_value(value):
    """Hex color strings become RGB arrays so they can be interpolated."""
    if isinstance(value, str) and value.startswith("#"):
        return np.array(hex_to_rgb(value))
    return value


class Timeline:
    """Animate named attributes between keyframes.

    Arguments:
        *keyframes: increasing times (any unit: frames, seconds, milliseconds).
        delay: offset added to every keyframe when evaluating.

    Attributes are declared by assignment. The value is a list with one entry per
    segment (``len(keyframes) - 1``), each entry being ``(easing, start, end)`` or
    ``(easing, value)`` for a constant segment. Hex color strings are interpolated
    as RGB.

    ``before`` and ``after`` hold attribute values returned outside the timeline
    (default: the first and last values). ``dtype`` maps an attribute name to a
    callable applied to its value, e.g. ``tl.dtype["count"] = int``.
    """

    def __init__(self, *keyframes, delay=0):
        if any(a > b for a, b in zip(keyframes, keyframes[1:])):
            raise ValueError("keyframes must be sorted")
        if len(keyframes) < 2:
            raise ValueError("a timeline needs at least two keyframes")
        self.keyframes = keyframes
        self.start = keyframes[0]
        self.end = keyframes[-1]
        self.delay_ = delay
        self.segments = [
            {"start": start, "end": end, "attributes": {}}
            for start, end in zip(keyframes, keyframes[1:])
        ]
        self.before = Attributes()
        self.after = Attributes()
        self.dtype = {}

    def __setattr__(self, name, value):
        if name in _RESERVED:
            super().__setattr__(name, value)
            return
        if len(value) != len(self.segments):
            raise ValueError(
                f"{name!r} needs {len(self.segments)} segment(s), got {len(value)}")
        for segment, entry in zip(self.segments, value):
            easing, *values = entry
            segment["attributes"][name] = (easing, *map(_parse_value, values))

    @property
    def attributes(self):
        return sorted({name for s in self.segments for name in s["attributes"]})

    def delay(self, delay):
        """Return a copy of the timeline shifted by ``delay``."""
        timeline = copy.deepcopy(self)
        timeline.delay_ += delay
        timeline.start += delay
        timeline.end += delay
        return timeline

    def grad(self, name, t=0, delta=1):
        """Finite-difference derivative of attribute ``name`` at time ``t``."""
        return (self[t + delta][name] - self[t][name]) / delta

    def _evaluate(self, segment, t_unit):
        attributes = Attributes()
        for name, (easing, *values) in segment["attributes"].items():
            value = tween(easing, *values, t=t_unit) if len(values) == 2 else values[0]
            if name in self.dtype:
                value = self.dtype[name](value)
            attributes[name] = value
        return attributes

    def _local_time(self, t):
        return t - self.delay_

    def __getitem__(self, t):
        """Evaluate every attribute at time ``t``. The result also carries ``t``."""
        local = self._local_time(t)
        if local < self.segments[0]["start"]:
            attributes = self.before or self._evaluate(self.segments[0], 0)
        elif local > self.segments[-1]["end"]:
            attributes = self.after or self._evaluate(self.segments[-1], 1)
        else:
            for segment in self.segments:
                start, end = segment["start"], segment["end"]
                if start <= local <= end:
                    duration = end - start
                    t_unit = (local - start) / duration if duration else 1.0
                    attributes = self._evaluate(segment, t_unit)
                    break
        attributes = Attributes(attributes)
        attributes.t = t
        return attributes


class Cycle(Timeline):
    """A timeline that repeats itself: time wraps around ``end``."""

    def _local_time(self, t):
        return self.start + (t - self.delay_ - self.start) % (self.end - self.start)


# ----------------------------------------------------------------------
# Helpers producing ``(values, frames)`` pairs for the ``animate_*`` methods
# ----------------------------------------------------------------------

def linear(start, end, frames, easing="linear"):
    """Values from ``start`` to ``end`` (numbers or vectors) over ``frames=(first, last)``."""
    first, last = frames
    t = np.linspace(0, 1, last - first + 1)
    values = tween(easing, np.asarray(start, dtype=float), np.asarray(end, dtype=float),
                   t[:, None] if np.ndim(start) else t)
    return list(values), list(range(first, last + 1))


def shake(frames, origin=(0, 0, 0), frequency=0.2, intensity=0.1, seed=0):
    """A random smooth jitter around ``origin``: ``frequency`` is the number of
    direction changes per frame, ``intensity`` the amplitude."""
    first, last = frames
    rng = np.random.default_rng(seed)
    count = max(int(round(frequency * (last - first))), 2)
    keyframes = np.linspace(first, last, count).astype(int)
    targets = rng.normal(scale=intensity, size=(count, 3))
    targets[0] = targets[-1] = 0
    timeline = Timeline(*keyframes)
    timeline.offset = [("cubic-in-out", targets[i], targets[i + 1]) for i in range(count - 1)]
    origin = np.asarray(origin, dtype=float)
    frames = list(range(first, last + 1))
    return [origin + timeline[f].offset for f in frames], frames


def flicker(steps, step_size=2, start_with=True):
    """Alternating booleans, ``step_size`` frames each, for ``animate_visibility``."""
    unit = [start_with] * step_size + [not start_with] * step_size
    return unit * steps


class Movement:
    """A path made of straight moves at constant speed, applied as location keyframes.

    ::

        path = Movement(speed=0.1).start_at(0, 0, 0).move_to(5, 0, 0).move_to(5, 5, 0)
        path.apply(cube)          # keyframes location (and heading when turn=True)
        path.duration             # number of frames
    """

    def __init__(self, speed=0.05, turn=False):
        self.speed = speed
        self.turn = turn
        self.frames = []
        self.headings = []

    def start_at(self, x, y, z):
        self.frames = [np.array((x, y, z), dtype=float)]
        self.headings = [0.0]
        return self

    def move_to(self, x, y, z):
        target = np.array((x, y, z), dtype=float)
        start = self.frames[-1]
        distance = float(np.linalg.norm(target - start))
        count = max(int(round(distance / self.speed)), 1)
        heading = float(np.degrees(np.arctan2(target[1] - start[1], target[0] - start[0])))
        for i in range(1, count + 1):
            self.frames.append(start + (target - start) * i / count)
            self.headings.append(heading)
        return self

    @property
    def duration(self):
        return len(self.frames)

    def apply(self, obj, start=0):
        frames = range(start, start + len(self.frames))
        obj.animate_location(self.frames, frames)
        if self.turn:
            obj.animate_rotation([(0, 0, h) for h in self.headings], frames)
        return obj
