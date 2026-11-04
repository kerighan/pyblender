"""Ready-made motions for the parts of a split :class:`~pyblender.text.Text`, or any objects.

Every function keyframes one channel (scale, location, rotation or visibility) per part,
starting at ``start`` and staggered by ``stagger`` frames from one part to the next::

    title = pb.Text("HELLO", split="letters", extrude=0.1)
    pop_in(title, start=0, duration=15, stagger=2, easing="back-out")
    wave(title, start=40, end=100, amplitude=0.1)
    pop_out(title, start=100)

Combine motions on different channels freely. Two motions on the same channel of
the same part overwrite each other where their frames overlap.
"""

import numpy as np

from .animation.easing import EASINGS
from .utils import to_degrees

__all__ = ["pop_in", "pop_out", "slide_in", "slide_out", "flip_in", "flip_out",
           "typewriter", "wave", "shake", "schedule"]


def _parts(items):
    return list(items.parts) if hasattr(items, "parts") else list(items)


def schedule(items, start=0, duration=20, stagger=3, easing="cubic-out", reverse=False):
    """Yield ``(part, frames, progress)`` for each part, with ``progress`` eased in [0, 1].

    Building block of every motion. ``reverse`` staggers from the last part to the first.
    """
    parts = _parts(items)
    order = reversed(parts) if reverse else parts
    t = np.linspace(0, 1, duration + 1)
    progress = np.asarray(EASINGS[easing](t), dtype=float)
    for i, part in enumerate(order):
        first = start + i * stagger
        yield part, range(first, first + duration + 1), progress


def _lerp(a, b, progress):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return a + (b - a) * progress[:, None]


def _set_hidden(part, hidden, frames):
    """Keyframe visibility: Blender keeps the value constant between these keyframes."""
    for attribute in ("hide_render", "hide_viewport"):
        part.animate(attribute, hidden, frames)


def _hide_before(part, frame):
    _set_hidden(part, [True, False], [frame - 1, frame])


def _hide_after(part, frame):
    _set_hidden(part, [False, True], [frame, frame + 1])


# ----------------------------------------------------------------------
# Scale
# ----------------------------------------------------------------------

def pop_in(items, start=0, duration=15, stagger=2, easing="back-out", scale_from=0.0, **kw):
    """Scale each part from ``scale_from`` to its current scale. Parts are invisible before."""
    for part, frames, progress in schedule(items, start, duration, stagger, easing, **kw):
        target = np.array(part.obj.scale)
        part.animate_scale(_lerp(target * scale_from, target, progress), frames)
    return items


def pop_out(items, start=0, duration=15, stagger=2, easing="back-in", scale_to=0.0, **kw):
    """Scale each part from its current scale to ``scale_to``, then hide it."""
    for part, frames, progress in schedule(items, start, duration, stagger, easing, **kw):
        current = np.array(part.obj.scale)
        part.animate_scale(_lerp(current, current * scale_to, progress), frames)
        _hide_after(part, frames[-1])
    return items


# ----------------------------------------------------------------------
# Location
# ----------------------------------------------------------------------

def slide_in(items, offset=(0, -1, 0), start=0, duration=20, stagger=2, easing="cubic-out", **kw):
    """Move each part from ``current + offset`` to its current location. Parts are hidden before.

    For an upright text, the local Y axis points up: ``offset=(0, -1, 0)`` rises from below.
    """
    for part, frames, progress in schedule(items, start, duration, stagger, easing, **kw):
        target = np.array(part.obj.location)
        part.animate_location(_lerp(target + offset, target, progress), frames)
        _hide_before(part, frames[0])
    return items


def slide_out(items, offset=(0, 1, 0), start=0, duration=20, stagger=2, easing="cubic-in", **kw):
    """Move each part from its current location to ``current + offset``, then hide it."""
    for part, frames, progress in schedule(items, start, duration, stagger, easing, **kw):
        current = np.array(part.obj.location)
        part.animate_location(_lerp(current, current + offset, progress), frames)
        _hide_after(part, frames[-1])
    return items


# ----------------------------------------------------------------------
# Rotation
# ----------------------------------------------------------------------

def flip_in(items, angle=(90, 0, 0), start=0, duration=20, stagger=2, easing="back-out",
            **kw):
    """Rotate each part from ``current + angle`` (degrees, per axis) to its current rotation.

    Parts are hidden before the motion starts.
    """
    for part, frames, progress in schedule(items, start, duration, stagger, easing, **kw):
        target = np.array(to_degrees(tuple(part.obj.rotation_euler)))
        part.animate_rotation(_lerp(target + angle, target, progress), frames)
        _hide_before(part, frames[0])
    return items


def flip_out(items, angle=(-90, 0, 0), start=0, duration=20, stagger=2, easing="back-in",
             **kw):
    """Rotate each part from its current rotation to ``current + angle``, then hide it."""
    for part, frames, progress in schedule(items, start, duration, stagger, easing, **kw):
        current = np.array(to_degrees(tuple(part.obj.rotation_euler)))
        part.animate_rotation(_lerp(current, current + angle, progress), frames)
        _hide_after(part, frames[-1])
    return items


# ----------------------------------------------------------------------
# Visibility and continuous motions
# ----------------------------------------------------------------------

def typewriter(items, start=0, stagger=3, **kw):
    """Make parts appear one after the other, without any transition."""
    for part, frames, _ in schedule(items, start, 1, stagger, "linear", **kw):
        _hide_before(part, frames[0])
    return items


def wave(items, start=0, end=60, amplitude=0.2, period=30, phase=0.6, axis=1):
    """Oscillate the parts along ``axis`` (0=X, 1=Y, 2=Z, in the parent's space).

    Each part lags the previous one by ``phase`` radians. ``period`` is in frames.
    """
    frames = range(start, end + 1)
    t = np.arange(len(frames))
    for i, part in enumerate(_parts(items)):
        base = np.array(part.obj.location)
        offsets = amplitude * np.sin(2 * np.pi * t / period - i * phase)
        values = np.repeat(base[None, :], len(frames), axis=0)
        values[:, axis] += offsets
        part.animate_location(values, frames)
    return items


def shake(items, start=0, end=30, amplitude=0.05, seed=0):
    """Random jitter of each part's location, decaying to rest at ``end``."""
    rng = np.random.default_rng(seed)
    frames = range(start, end + 1)
    decay = np.linspace(1, 0, len(frames))
    for part in _parts(items):
        base = np.array(part.obj.location)
        jitter = rng.uniform(-1, 1, (len(frames), 3)) * amplitude * decay[:, None]
        jitter[-1] = 0
        part.animate_location(base[None, :] + jitter, frames)
    return items
