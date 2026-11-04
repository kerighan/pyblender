"""pyblender: a small declarative layer over ``bpy`` to script Blender scenes.

Importing the package inside Blender resets it to an empty scene, so a script run with
``blender -b --python my_scene.py`` only contains what it creates.

Outside Blender (no ``bpy``), only :mod:`pyblender.animation` and the ``pyblender``
command are available.
"""

try:
    import bpy
except ImportError:  # outside Blender
    bpy = None

__all__ = ["reset"]

if bpy is not None:
    from .base import Empty
    from .camera import Camera
    from .force import Turbulence, Vortex
    from .image import Image
    from .light import PointLight, SpotLight, Sun
    from .material import Material, NodeMaterial, VolumeMaterial
    from .mesh import Cube, Cylinder, Grid, IcoSphere, Line, Plane, Sphere
    from .modifier import Displacement, Subdivision
    from .particles import ParticleSystem
    from .post import PostProcess
    from .scene import Scene
    from .text import Text
    from .utils import hex_to_rgb, hex_to_rgba

    __all__ += [
        "Camera", "Cube", "Cylinder", "Displacement", "Empty", "Grid", "IcoSphere", "Image",
        "Line", "Material", "NodeMaterial", "ParticleSystem", "Plane", "PointLight", "PostProcess",
        "Scene",
        "Sphere", "SpotLight", "Subdivision", "Sun", "Text", "Turbulence", "VolumeMaterial",
        "Vortex",
        "hex_to_rgb", "hex_to_rgba",
    ]


def reset():
    """Replace the current scene with an empty one. No-op outside Blender."""
    if bpy is not None:
        bpy.ops.wm.read_factory_settings(use_empty=True)


reset()
