import bpy

from .base import BlenderObject, link_to_scene
from .utils import to_rgb


class Light(BlenderObject):
    """Base class for lights. Use :class:`Sun`, :class:`PointLight` or :class:`SpotLight`."""

    light_type = None

    def __init__(self, location=(0, 0, 0), energy=50, color=None, rotation=None, focus_point=None):
        data = bpy.data.lights.new("light", type=self.light_type)
        data.energy = energy
        if color is not None:
            data.color = to_rgb(color)

        self.data = data
        self.obj = link_to_scene(bpy.data.objects.new("light", data))
        self.obj.location = location
        if rotation is not None:
            self.obj.rotation_euler = rotation
        if focus_point is not None:
            self.look_at(focus_point)

    def animate_energy(self, values, frames=None):
        return self.animate("energy", values, frames, data=self.data)


class Sun(Light):
    """Directional light. Its ``rotation`` or ``focus_point`` sets the direction."""

    light_type = "SUN"

    def __init__(self, energy=5, color=None, rotation=None, focus_point=None, location=(0, 0, 10)):
        super().__init__(location, energy, color, rotation, focus_point)


class PointLight(Light):
    """Omnidirectional light. ``radius`` is the size of the emitter and softens shadows."""

    light_type = "POINT"

    def __init__(self, location=(0, 0, 0), energy=50, color=None, radius=0.1):
        super().__init__(location, energy, color)
        self.data.shadow_soft_size = radius


class SpotLight(Light):
    """Cone light.

    Arguments:
        size: cone angle in radians.
        blend: softness of the cone edge, between 0 and 1.
        radius: size of the emitter, softens shadows.
    """

    light_type = "SPOT"

    def __init__(
        self,
        location=(0, 0, 0),
        energy=50,
        color=None,
        rotation=None,
        focus_point=None,
        size=0.785,
        blend=0.15,
        radius=0.1,
    ):
        super().__init__(location, energy, color, rotation, focus_point)
        self.data.spot_size = size
        self.data.spot_blend = blend
        self.data.shadow_soft_size = radius
