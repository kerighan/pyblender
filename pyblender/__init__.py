"""pyblender: a declarative layer over ``bpy`` to script Blender scenes and motion graphics.

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
    from .base import Empty, Group
    from .camera import Camera
    from .curve import Bezier, BezierCircle
    from .force import ForceField, Turbulence, Vortex, Wind
    from .geometry import Geometry
    from .light import AreaLight, PointLight, SpotLight, Sun
    from .material import (DiffuseMaterial, EmissionMaterial, Material, NodeMaterial,
                           RefractionMaterial, VolumeMaterial)
    from .mesh import (Box, Circle, Cone, Cube, Cylinder, Grid, IcoSphere, Line, Mesh, Model,
                       Plane, Sphere, Torus, UVSphere, merge)
    from .particles import ParticleSystem
    from .post import PostProcess
    from .quick import auto_camera, auto_light, post, render, scene
    from .scene import Scene, defaults
    from .text import Text
    from .texture import Image, Noise, Texture
    from .utils import hex_to_rgb, hex_to_rgba

    __all__ += [
        "AreaLight", "Bezier", "BezierCircle", "Box", "Camera", "Circle", "Cone", "Cube",
        "Cylinder", "DiffuseMaterial", "EmissionMaterial", "Empty", "ForceField", "Geometry",
        "Grid", "Group", "IcoSphere", "Image", "Line", "Material", "Mesh", "Model",
        "NodeMaterial", "Noise", "ParticleSystem", "Plane", "PointLight", "PostProcess",
        "RefractionMaterial", "Scene", "Sphere", "SpotLight", "Sun", "Text", "Texture", "Torus",
        "Turbulence", "UVSphere", "VolumeMaterial", "Vortex", "Wind", "auto_camera",
        "auto_light", "defaults", "hex_to_rgb", "hex_to_rgba", "merge", "post", "render", "scene",
    ]


def reset():
    """Replace the current scene with an empty one. No-op outside Blender."""
    if bpy is not None:
        from .quick import _reset
        bpy.ops.wm.read_factory_settings(use_empty=True)
        _reset()


reset()
