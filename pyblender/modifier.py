import bpy

# Wireframe
# Screw
# Array
# Ocean
# Wave


class Displacement:
    def __init__(self, instance, img_inst, strength=1):
        obj = instance.obj
        img = img_inst.img

        if 'Disp' not in obj.modifiers:
            m = obj.modifiers.new('Disp', 'DISPLACE')
            print("here")

        m = obj.modifiers["Disp"]
        m.strength = strength

        if not m.texture:
            t = bpy.data.textures.new("DispTex", "IMAGE")

        t = bpy.data.textures["DispTex"]

        t.image = img
        m.texture = t
        self.modifier = m
