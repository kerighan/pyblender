import bpy

from .base import BlenderObject


class Force(BlenderObject):
    """Base class for force fields acting on particles.

    Use :class:`Vortex` or :class:`Turbulence`.
    """

    force_type = None

    def __init__(self, location=(0, 0, 0), strength=1.0, noise=0.0, flow=0.0):
        bpy.ops.object.effector_add(type=self.force_type, location=location)
        self.obj = bpy.context.active_object
        self.field = self.obj.field
        self.field.strength = strength
        self.field.noise = noise
        self.field.flow = flow


class Vortex(Force):
    force_type = "VORTEX"


class Turbulence(Force):
    force_type = "TURBULENCE"
