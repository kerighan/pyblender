"""Small helpers shared across the package."""


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
    """Accept a hex string or an ``(r, g, b)`` sequence of floats in [0, 1]."""
    if isinstance(color, str):
        return hex_to_rgb(color)
    return tuple(float(c) for c in color[:3])


def to_rgba(color, alpha=1.0):
    return (*to_rgb(color), alpha)


def look_at(obj, point):
    """Rotate ``obj`` so that its local -Z axis points towards ``point``.

    This is the convention used by cameras and lights in Blender.
    """
    import mathutils  # only available inside Blender

    direction = mathutils.Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
