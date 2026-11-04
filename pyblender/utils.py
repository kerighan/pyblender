"""Small helpers shared across the package."""

import math
import random
import string


def hex_to_rgb(value):
    """Convert a ``#RRGGBB`` string to an ``(r, g, b)`` tuple of floats in [0, 1]."""
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected a 6-digit hex color, got {value!r}")
    return tuple(int(value[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def hex_to_rgba(value, alpha=1.0):
    """Convert a hex color string to an ``(r, g, b, a)`` tuple."""
    return (*hex_to_rgb(value), alpha)


def to_rgb(color):
    """Accept a hex string or an ``(r, g, b[, a])`` sequence of floats in [0, 1]."""
    if isinstance(color, str):
        return hex_to_rgb(color)
    return tuple(float(c) for c in color[:3])


def to_rgba(color, alpha=1.0):
    if not isinstance(color, str) and len(color) == 4:
        return tuple(float(c) for c in color)
    return (*to_rgb(color), alpha)


def to_radians(rotation):
    """Convert a rotation given in degrees (scalar or per-axis sequence) to radians."""
    if isinstance(rotation, (int, float)):
        return math.radians(rotation)
    return tuple(math.radians(r) for r in rotation)


def to_degrees(rotation):
    if isinstance(rotation, (int, float)):
        return math.degrees(rotation)
    return tuple(math.degrees(r) for r in rotation)


def look_at(obj, point):
    """Rotate ``obj`` so that its local -Z axis points towards ``point``.

    This is the convention used by cameras and lights in Blender.
    """
    import mathutils  # only available inside Blender

    direction = mathutils.Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def random_string(length=8):
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


DIRECTIONS = {
    "up": (0, 0, 1), "down": (0, 0, -1), "front": (1, 0, 0), "back": (-1, 0, 0),
    "right": (0, 1, 0), "left": (0, -1, 0),
}


def faces_direction(normal, direction, limit=0.5):
    """True when ``normal`` points roughly towards ``direction`` (a name or a vector)."""
    import mathutils

    if isinstance(direction, str):
        direction = DIRECTIONS[direction]
    return mathutils.Vector(direction).dot(normal) > limit
