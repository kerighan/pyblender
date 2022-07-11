import bpy
import numpy as np

from .utils import hex_to_rgb, look_at


class Sun:
    def __init__(self, energy=1, location=(30, -4, 5)):
        light_data = bpy.data.lights.new('light', type='SUN')
        light = bpy.data.objects.new('light', light_data)
        light.location = location
        light.data.energy = energy
        bpy.context.collection.objects.link(light)
        self.obj = light


class PointLight:
    def __init__(self, location, energy=50, color=None, attenuation=1):
        light_data = bpy.data.lights.new('light', type='POINT')
        light = bpy.data.objects.new('light', light_data)
        light.location = location
        light.data.energy = energy
        light.data.quadratic_attenuation = attenuation
        self.light_data = light_data
        if color is not None:
            light.data.color = hex_to_rgb(color)
        bpy.context.collection.objects.link(light)
        self.obj = light

    def animate_energy(self, values, frames=None):
        if frames is None:
            frames = range(len(values))

        for frame, energy in zip(frames, values):
            self.light_data.energy = energy
            self.light_data.keyframe_insert("energy", frame=frame)


class SpotLight:
    def __init__(
        self, location, rotation=(0, 0, 0), energy=50, color=None,
        focus_point=None, attenuation=1, blend=.15, size=0.785398
    ):
        light_data = bpy.data.lights.new('light', type='SPOT')
        light = bpy.data.objects.new('light', light_data)
        light.location = location
        if focus_point is None:
            light.rotation_euler = rotation
        else:
            look_at(light, focus_point)
        light.data.energy = energy
        light.data.constant_coefficient = attenuation
        light.data.spot_blend = blend
        light.data.spot_size = size

        self.light_data = light_data
        if color is not None:
            light.data.color = hex_to_rgb(color)

        bpy.context.collection.objects.link(light)
        self.obj = light

    def animate_energy(self, values, frames=None):
        if frames is None:
            frames = range(len(values))

        for frame, energy in zip(frames, values):
            self.light_data.energy = energy
            self.light_data.keyframe_insert("energy", frame=frame)

    def look_at(self, item):
        if isinstance(item, tuple):
            look_at(self.obj, item)
        else:
            constraint = self.obj.constraints.new(type='TRACK_TO')
            constraint.target = item.obj
