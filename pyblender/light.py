import math

import bpy

from .base import BlenderObject, link_to_scene
from .utils import to_radians, to_rgb


class Light(BlenderObject):
    """Base class for lights. Use :class:`Sun`, :class:`PointLight`, :class:`SpotLight`
    or :class:`AreaLight`."""

    light_type = None

    def __init__(self, location=(0, 0, 0), energy=50, color=None, rotation=None,
                 focus_point=None):
        data = bpy.data.lights.new("light", type=self.light_type)
        data.energy = energy
        if color is not None:
            data.color = to_rgb(color)

        self.data = data
        self.obj = link_to_scene(bpy.data.objects.new("light", data))
        self.obj.location = location
        if rotation is not None:
            self.obj.rotation_euler = to_radians(rotation)
        if focus_point is not None:
            self.look_at(focus_point)

    def animate_energy(self, values, frames=None):
        return self.animate("energy", values, frames, data=self.data)

    def animate_color(self, values, frames=None):
        return self.animate("color", [to_rgb(v) for v in values], frames, data=self.data)


class Sun(Light):
    """Directional light. Its ``rotation`` or ``focus_point`` sets the direction."""

    light_type = "SUN"

    def __init__(self, energy=5, color=None, rotation=None, focus_point=None,
                 location=(0, 0, 10), angle=0.5):
        super().__init__(location, energy, color, rotation, focus_point)
        self.data.angle = math.radians(angle)


class PointLight(Light):
    """Omnidirectional light. ``radius`` is the size of the emitter and softens shadows."""

    light_type = "POINT"

    def __init__(self, location=(0, 0, 0), energy=50, color=None, radius=0.1):
        super().__init__(location, energy, color)
        self.data.shadow_soft_size = radius


class SpotLight(Light):
    """Cone light.

    Arguments:
        angle: full cone angle in degrees.
        blend: softness of the cone edge, between 0 and 1.
        radius: size of the emitter, softens shadows.
    """

    light_type = "SPOT"

    def __init__(self, location=(0, 0, 0), energy=50, color=None, rotation=None,
                 focus_point=None, angle=45, blend=0.15, radius=0.1):
        super().__init__(location, energy, color, rotation, focus_point)
        self.data.spot_size = math.radians(angle)
        self.data.spot_blend = blend
        self.data.shadow_soft_size = radius


class AreaLight(Light):
    """Rectangular soft light (a softbox). ``size`` is ``(width, height)``."""

    light_type = "AREA"

    def __init__(self, location=(0, 0, 0), energy=100, color=None, rotation=None,
                 focus_point=None, size=(1, 1)):
        super().__init__(location, energy, color, rotation, focus_point)
        self.data.shape = "RECTANGLE"
        self.data.size, self.data.size_y = size
