"""Zero-configuration helpers: ``pb.render("out.png")`` with an automatic camera and light.

::

    import pyblender as pb
    pb.Cube(material="#FF5500")
    pb.render("cube.png")                     # auto camera framing the scene, default light
    pb.post.vignette(0.4)                     # post-processing of the default scene
    pb.render("spin.mp4", frames=120)

``pb.scene()`` returns the default :class:`~pyblender.scene.Scene` (created on first use),
so everything stays overridable: create your own ``Camera`` or ``Scene`` and the helpers
use them.
"""

import math

import bpy
from mathutils import Vector

from .scene import Scene

_scene = None


def scene(**kwargs):
    """The default scene, created on first use (``kwargs`` go to :class:`Scene` then)."""
    global _scene
    if _scene is None:
        _scene = Scene(**kwargs)
    elif kwargs:
        raise ValueError("the default scene already exists, use pb.scene() without arguments")
    return _scene


def _reset():
    global _scene
    _scene = None


def bounds(objects=None):
    """World-space bounding box ``(min, max)`` of the renderable objects."""
    corners = []
    for obj in objects or bpy.context.scene.objects:
        if obj.type in ("MESH", "CURVE", "FONT", "SURFACE", "META") and not obj.hide_render:
            corners += [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    if not corners:
        return Vector((-1, -1, -1)), Vector((1, 1, 1))
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return low, high


def auto_camera(direction=(0.6, -1.0, 0.5), lens=50, margin=1.15):
    """A camera framing every object from a three-quarter view (``direction`` from the
    centre of the scene)."""
    from .camera import Camera

    low, high = bounds()
    center = (low + high) / 2
    radius = max((high - low).length / 2, 0.5)
    fov = 2 * math.atan(18 / lens)  # 36 mm sensor
    distance = radius * margin / math.sin(fov / 2)
    location = center + Vector(direction).normalized() * distance
    return Camera(tuple(location), target=tuple(center), lens=lens)


def auto_light():
    """A soft sun and a dim grey world, when the scene has no light at all."""
    from .light import Sun

    low, high = bounds()
    center = (low + high) / 2
    Sun(energy=3, angle=10, target=tuple(center),
        location=tuple(center + Vector((3, -4, 6)) * max((high - low).length, 1)))
    if bpy.context.scene.world is None:  # keep a background the script already chose
        scene().set_background("#404040", strength=1.0)


def render(filename, **kwargs):
    """Render with the default scene, adding a camera and a light when the scene has none.
    ``kwargs`` are those of :meth:`Scene.render` (``frames=120`` for an animation)."""
    current = scene()
    if bpy.context.scene.camera is None:
        auto_camera()
    if not any(obj.type == "LIGHT" for obj in bpy.context.scene.objects):
        auto_light()
    return current.render(filename, **kwargs)


class _PostProxy:
    """``pb.post``: the post-processing stack of the default scene."""

    def __getattr__(self, name):
        return getattr(scene().post, name)

    def __repr__(self):
        return repr(scene().post)


post = _PostProxy()
