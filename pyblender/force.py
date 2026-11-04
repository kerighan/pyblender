import bpy

from .base import BlenderObject
from .utils import to_radians


class Force(BlenderObject):
    """Base class for force fields acting on particles and physics.

    Use :class:`Vortex`, :class:`Turbulence`, :class:`Wind` or :class:`ForceField`.
    """

    force_type = None

    def __init__(self, location=(0, 0, 0), rotation=(0, 0, 0), strength=1.0, noise=0.0,
                 flow=0.0, size=0.0, falloff=0.0):
        bpy.ops.object.effector_add(type=self.force_type, location=location,
                                    rotation=to_radians(rotation))
        self.obj = bpy.context.active_object
        self.field = self.obj.field
        self.field.strength = strength
        self.field.noise = noise
        self.field.flow = flow
        self.field.size = size
        self.field.falloff_power = falloff

    def animate_strength(self, values, frames=None):
        return self.animate("strength", values, frames, data=self.field)


class Vortex(Force):
    force_type = "VORTEX"


class Turbulence(Force):
    force_type = "TURBULENCE"


class Wind(Force):
    """Blows along the local Z axis: orient it with ``rotation`` or ``look_at``."""

    force_type = "WIND"


class ForceField(Force):
    """Attracts (negative strength) or repels particles from a point."""

    force_type = "FORCE"
