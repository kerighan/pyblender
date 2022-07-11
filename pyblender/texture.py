import os

import bpy

execution_dir = os.getcwd()
# print(os.path.abspath(os.path.dirname(__file__)))


class Image:
    def __init__(self, src):
        self.img = bpy.data.images.load(os.path.join(
            execution_dir, src), check_existing=False)


class Texture:
    def __init__(self, src, name="Texture"):
        img = bpy.data.images.load(src, check_existing=False)
        t = bpy.data.textures.new(name, "IMAGE")
        t.image = img
        self.texture = t


class Noise:
    def __init__(
        self, type="DISTORTED_NOISE",
        noise_basis="BLENDER_ORIGINAL", noise_distortion="BLENDER_ORIGINAL",
        noise_scale=.25, distortion=1., nabla=.025, intensity=1, name="noise"
    ):
        t = bpy.data.textures.new(name=name, type=type)
        t.distortion = distortion
        t.nabla = nabla
        t.intensity = intensity
        t.noise_scale = noise_scale
        t.noise_basis = noise_basis
        t.noise_distortion = noise_distortion
        self.texture = t
