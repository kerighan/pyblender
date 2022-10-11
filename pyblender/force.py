import bpy


class Force:
    def set_strength(self, strength):
        self.force.field.strength = strength

    def set_noise(self, noise):
        self.force.field.noise = noise

    def set_flow(self, flow):
        self.force.field.flow = flow

    def set_size(self, size):
        self.force.field.size = size


class Vortex(Force):
    def __init__(self, location=(0, 0, 0), strength=1, noise=0, flow=0):
        bpy.ops.object.effector_add(type="VORTEX", location=location)
        self.force = bpy.context.object

        self.set_strength(strength)
        self.set_noise(noise)
        self.set_flow(flow)


class Turbulence(Force):
    def __init__(self,
                 location=(0, 0, 0),
                 strength=1,
                 size=0,
                 noise=0,
                 flow=0):
        bpy.ops.object.effector_add(type="TURBULENCE", location=location)
        self.force = bpy.context.object

        self.set_strength(strength)
        self.set_noise(noise)
        self.set_size(size)
        self.set_flow(flow)
