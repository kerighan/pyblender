"""Images and procedural textures used by materials, modifiers and the compositor."""

import os

import bpy


class Image:
    """An image loaded from disk: material texture, displacement map or compositor input."""

    def __init__(self, path, color_space="sRGB"):
        self.img = bpy.data.images.load(os.path.abspath(path), check_existing=True)
        self.img.colorspace_settings.name = color_space


class Texture:
    """An image texture datablock, for modifiers (displacement) and particles."""

    def __init__(self, path, name="texture"):
        if isinstance(path, Image):
            self.image = path
        else:
            self.image = Image(path)
        self.texture = bpy.data.textures.new(name, "IMAGE")
        self.texture.image = self.image.img


class Noise:
    """A procedural noise texture datablock (clouds, distorted noise, marble, wood...).

    Arguments:
        kind: ``"CLOUDS"``, ``"DISTORTED_NOISE"``, ``"MARBLE"``, ``"WOOD"``, ``"MUSGRAVE"``,
            ``"VORONOI"``, ``"STUCCI"``, ``"NOISE"``...
        scale: feature size of the noise.
        basis: ``"BLENDER_ORIGINAL"``, ``"PERLIN"``, ``"VORONOI_F1"``...
    """

    def __init__(self, kind="DISTORTED_NOISE", scale=0.25, basis="BLENDER_ORIGINAL",
                 distortion=1.0, intensity=1.0, depth=2, name="noise", **properties):
        texture = bpy.data.textures.new(name, kind)
        texture.intensity = intensity
        for key, value in dict(noise_scale=scale, noise_basis=basis, distortion=distortion,
                               noise_depth=depth, **properties).items():
            if hasattr(texture, key):
                setattr(texture, key, value)
        self.texture = texture
