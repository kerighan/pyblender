"""Materials, from one-line PBR presets to full shader node graphs."""

import bpy

from .nodes import Node, NodeTree
from .texture import Image
from .utils import to_rgba


class NodeMaterial(NodeTree):
    """A node-based material.

    ``NodeMaterial()`` starts with a Principled BSDF (``self.bsdf``) wired to the
    output (``self.output``). ``NodeMaterial(material=existing)`` wraps an existing
    ``bpy`` material, for instance from an imported model.
    """

    def __init__(self, name="material", material=None):
        self.mat = bpy.data.materials.new(name=name) if material is None else material
        self.mat.use_nodes = True
        self.nodes = self.mat.node_tree.nodes
        self.links = self.mat.node_tree.links
        bsdf = self.nodes.get("Principled BSDF")
        output = self.nodes.get("Material Output")
        self.bsdf = Node(bsdf, self) if bsdf else None
        self.output = Node(output, self) if output else None

    @property
    def name(self):
        return self.mat.name

    def reset(self):
        """Remove every node, keeping only a fresh Material Output."""
        self.clear()
        self.output = self.create("ShaderNodeOutputMaterial")
        self.bsdf = None
        return self

    def set_shadows(self, cast_shadows=True, shadow_mode=None):
        """Eevee shadow mode: ``"NONE"``, ``"OPAQUE"``, ``"CLIP"`` or ``"HASHED"``."""
        if shadow_mode is not None:
            self.mat.shadow_method = shadow_mode
        elif not cast_shadows:
            self.mat.shadow_method = "NONE"
        return self

    def set_displacement(self, method="BUMP"):
        """Cycles displacement method: ``"BUMP"``, ``"DISPLACEMENT"`` or ``"BOTH"``."""
        self.mat.cycles.displacement_method = method
        return self

    # ------------------------------------------------------------------
    # Shaders
    # ------------------------------------------------------------------

    def create_principled_bsdf(self):
        return self.create("ShaderNodeBsdfPrincipled")

    def create_diffuse_bsdf(self):
        return self.create("ShaderNodeBsdfDiffuse")

    def create_transparent_bsdf(self):
        return self.create("ShaderNodeBsdfTransparent")

    def create_glass_bsdf(self, ior=1.45, roughness=0.0):
        node = self.create("ShaderNodeBsdfGlass")
        node["IOR"] = ior
        node["Roughness"] = roughness
        return node

    def create_refraction_bsdf(self, ior=1.45, roughness=0.0):
        node = self.create("ShaderNodeBsdfRefraction")
        node["IOR"] = ior
        node["Roughness"] = roughness
        return node

    def create_emission(self, strength=1.0, color="#FFFFFF"):
        node = self.create("ShaderNodeEmission")
        node["Strength"] = strength
        node["Color"] = color
        return node

    def create_volume_scatter(self, density=1.0):
        node = self.create("ShaderNodeVolumeScatter")
        node["Density"] = density
        return node

    def create_volume_principled(self):
        return self.create("ShaderNodeVolumePrincipled")

    def create_mix_shader(self, fac=0.5):
        node = self.create("ShaderNodeMixShader")
        node["Fac"] = fac
        return node

    def create_add_shader(self):
        return self.create("ShaderNodeAddShader")

    def create_shader_to_rgb(self):
        return self.create("ShaderNodeShaderToRGB")

    # ------------------------------------------------------------------
    # Inputs and vectors
    # ------------------------------------------------------------------

    def create_texture_coordinate(self, use_mapping=True):
        """Texture coordinates, with a Mapping node wired to ``Generated`` by default.

        Returns ``(coordinates, mapping)`` when ``use_mapping`` else the coordinates node.
        """
        node = self.create("ShaderNodeTexCoord")
        if use_mapping:
            mapping = self.create_mapping()
            node["Generated"].to(mapping["Vector"])
            return node, mapping
        return node

    def create_mapping(self, location=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)):
        node = self.create("ShaderNodeMapping")
        node["Location"] = location
        node["Rotation"] = rotation
        node["Scale"] = scale
        return node

    def create_geometry(self):
        return self.create("ShaderNodeNewGeometry")

    def create_camera_data(self):
        return self.create("ShaderNodeCameraData")

    def create_layer_weight(self, blend=0.5):
        node = self.create("ShaderNodeLayerWeight")
        node["Blend"] = blend
        return node

    def create_fresnel(self, ior=1.45):
        node = self.create("ShaderNodeFresnel")
        node["IOR"] = ior
        return node

    def create_ambient_occlusion(self, samples=16):
        return self.create("ShaderNodeAmbientOcclusion", samples=samples)

    def create_bevel(self, radius=0.05, samples=4):
        node = self.create("ShaderNodeBevel", samples=samples)
        node["Radius"] = radius
        return node

    def create_normal_map(self, texture=None, strength=1.0):
        node = self.create("ShaderNodeNormalMap")
        node["Strength"] = strength
        if texture is not None:
            texture["Color"].to(node["Color"])
        return node

    def create_bump(self, strength=1.0, distance=1.0):
        node = self.create("ShaderNodeBump")
        node["Strength"] = strength
        node["Distance"] = distance
        return node

    def create_displacement(self, scale=1.0, midlevel=0.5):
        node = self.create("ShaderNodeDisplacement")
        node["Scale"] = scale
        node["Midlevel"] = midlevel
        return node

    # ------------------------------------------------------------------
    # Color
    # ------------------------------------------------------------------

    def create_hue_saturation(self, hue=0.5, saturation=1.0, value=1.0, fac=1.0):
        node = self.create("ShaderNodeHueSaturation")
        node["Hue"] = hue
        node["Saturation"] = saturation
        node["Value"] = value
        node["Fac"] = fac
        return node

    def create_bright_contrast(self, bright=0.0, contrast=0.0):
        node = self.create("ShaderNodeBrightContrast")
        node["Bright"] = bright
        node["Contrast"] = contrast
        return node

    def create_separate_hsv(self):
        return self.create("ShaderNodeSeparateHSV")

    def create_combine_hsv(self):
        return self.create("ShaderNodeCombineHSV")

    def create_separate_rgb(self):
        return self.create("ShaderNodeSeparateRGB")

    def create_combine_rgb(self):
        return self.create("ShaderNodeCombineRGB")

    # ------------------------------------------------------------------
    # Textures
    # ------------------------------------------------------------------

    def create_texture(self, image, projection="FLAT", extension="REPEAT", color_space="sRGB",
                       interpolation="Linear", frame_offset=0):
        """An image texture. ``image`` is a path or an :class:`~pyblender.texture.Image`."""
        if isinstance(image, str):
            image = Image(image, color_space=color_space)
        node = self.create("ShaderNodeTexImage", projection=projection, extension=extension,
                           interpolation=interpolation)
        node.node.image = image.img
        node.node.image_user.frame_offset = frame_offset
        return node

    create_image_texture = create_texture

    def create_noise_texture(self, scale=5.0, detail=2.0, roughness=0.5, distortion=0.0,
                             dimensions="3D"):
        node = self.create("ShaderNodeTexNoise", noise_dimensions=dimensions)
        node["Scale"] = scale
        node["Detail"] = detail
        node["Roughness"] = roughness
        node["Distortion"] = distortion
        return node

    def create_musgrave_texture(self, scale=5.0, detail=2.0, dimension=2.0, lacunarity=2.0,
                                offset=0.0, gain=1.0, kind="MULTIFRACTAL", dimensions="3D"):
        node = self.create("ShaderNodeTexMusgrave", musgrave_type=kind,
                           musgrave_dimensions=dimensions)
        for name, value in dict(Scale=scale, Detail=detail, Dimension=dimension,
                                Lacunarity=lacunarity, Offset=offset, Gain=gain).items():
            node[name] = value
        return node

    def create_voronoi_texture(self, scale=5.0, randomness=1.0, distance="EUCLIDEAN",
                               feature="F1", dimensions="3D"):
        node = self.create("ShaderNodeTexVoronoi", distance=distance, feature=feature,
                           voronoi_dimensions=dimensions)
        node["Scale"] = scale
        node["Randomness"] = randomness
        return node

    def create_wave_texture(self, scale=5.0, distortion=1.0, detail=2.0, detail_scale=1.0,
                            detail_roughness=0.5, phase_offset=0.0, kind="BANDS",
                            profile="SIN", direction="X"):
        node = self.create("ShaderNodeTexWave", wave_type=kind, wave_profile=profile)
        if kind == "BANDS":
            node.node.bands_direction = direction
        else:
            node.node.rings_direction = direction
        for name, value in {"Scale": scale, "Distortion": distortion, "Detail": detail,
                            "Detail Scale": detail_scale, "Detail Roughness": detail_roughness,
                            "Phase Offset": phase_offset}.items():
            node[name] = value
        return node

    def create_magic_texture(self, scale=5.0, distortion=1.0, depth=2):
        node = self.create("ShaderNodeTexMagic", turbulence_depth=depth)
        node["Scale"] = scale
        node["Distortion"] = distortion
        return node

    def create_gradient_texture(self, kind="LINEAR"):
        return self.create("ShaderNodeTexGradient", gradient_type=kind)

    def create_checker_texture(self, scale=5.0, color1="#FFFFFF", color2="#000000"):
        node = self.create("ShaderNodeTexChecker")
        node["Scale"] = scale
        node["Color1"] = color1
        node["Color2"] = color2
        return node

    def create_brick_texture(self, scale=5.0):
        node = self.create("ShaderNodeTexBrick")
        node["Scale"] = scale
        return node

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def animate_color(self, values, frames=None, socket="Base Color"):
        """Keyframe a color socket of the main shader from a list of colors."""
        return self.bsdf.animate(socket, values, frames)

    def _set_or_link(self, socket, value):
        """Set a BSDF socket from a number/color, or from an image path / texture node."""
        if value is None:
            return
        if isinstance(value, str) and not value.startswith("#"):
            self.create_texture(value)["Color"].to(self.bsdf[socket])
        elif isinstance(value, Node):
            value.to(self.bsdf[socket])
        elif isinstance(value, Image):
            self.create_texture(value)["Color"].to(self.bsdf[socket])
        else:
            self.bsdf[socket] = value


class Material(NodeMaterial):
    """A Principled BSDF material.

    Numeric arguments accept a value, an image path, an :class:`~pyblender.texture.Image`
    or a node (its ``Color`` output is linked).

    Arguments:
        color: base color.
        roughness, metallic, specular, transmission, subsurface: PBR inputs in [0, 1].
        opacity: alpha, below 1 enables Eevee alpha blending.
        emission_strength, emission_color: glow (defaults to ``color``).
        texture: image used as base color.
        normal: normal map image path or node.
        displacement, displacement_scale: height map driving true displacement.
        cast_shadows, shadow_mode, blend_mode: Eevee shadow and blend settings.
    """

    def __init__(self, color="#FFFFFF", roughness=0.5, metallic=0.5, specular=0.0, opacity=1.0,
                 transmission=0.0, subsurface=0.0, emission_strength=0.0, emission_color=None,
                 texture=None, normal=None, displacement=None, displacement_scale=1.0,
                 cast_shadows=True, shadow_mode=None, blend_mode=None, name="material"):
        super().__init__(name)
        self.bsdf["Base Color"] = color
        for socket, value in {"Roughness": roughness, "Metallic": metallic, "Specular": specular,
                              "Transmission": transmission, "Subsurface": subsurface}.items():
            self._set_or_link(socket, value)
        self._set_or_link("Base Color", texture)

        if normal is not None:
            normal_map = self.create_normal_map()
            if isinstance(normal, Node):
                normal.to(normal_map["Color"])
            else:
                texture = self.create_texture(normal, color_space="Non-Color")
                texture["Color"].to(normal_map["Color"])
            normal_map["Normal"].to(self.bsdf["Normal"])

        if opacity != 1:
            self.bsdf["Alpha"] = opacity
            blend_mode = blend_mode or "BLEND"
        if blend_mode is not None:
            self.mat.blend_method = blend_mode
        self.set_shadows(cast_shadows, shadow_mode)

        if emission_strength > 0:
            self.bsdf["Emission"] = to_rgba(emission_color or color)
            self.bsdf["Emission Strength"] = emission_strength

        if displacement is not None:
            height = self.create_texture(displacement, color_space="Non-Color")
            node = self.create_displacement(scale=displacement_scale)
            height["Color"].to(node["Height"])
            node["Displacement"].to(self.output["Displacement"])
            self.set_displacement("BOTH")


class DiffuseMaterial(NodeMaterial):
    """A plain Diffuse BSDF, cheaper than :class:`Material`."""

    def __init__(self, color="#FFFFFF", roughness=0.5, texture=None, normal=None,
                 blend_mode="OPAQUE"):
        super().__init__("diffuse")
        self.reset()
        self.bsdf = self.create_diffuse_bsdf()
        self.bsdf["BSDF"].to(self.output["Surface"])
        self.bsdf["Color"] = color
        self.bsdf["Roughness"] = roughness
        if texture is not None:
            self.create_texture(texture)["Color"].to(self.bsdf["Color"])
        if normal is not None:
            texture = self.create_texture(normal, color_space="Non-Color")
            normal_map = self.create_normal_map(texture)
            normal_map["Normal"].to(self.bsdf["Normal"])
        self.mat.blend_method = blend_mode


class EmissionMaterial(NodeMaterial):
    """A pure emitter: unlit color, for neon, screens and light sources."""

    def __init__(self, color="#FFFFFF", strength=1.0, cast_shadows=True, shadow_mode=None):
        super().__init__("emission")
        self.reset()
        self.bsdf = self.create_emission(strength=strength, color=color)
        self.bsdf["Emission"].to(self.output["Surface"])
        self.set_shadows(cast_shadows, shadow_mode)


class RefractionMaterial(NodeMaterial):
    """A Refraction BSDF: glass-like refraction without reflections.

    In Eevee, ``screen_refraction`` needs ``Scene.set_eevee(ssr=True, refraction=True)``.
    """

    def __init__(self, color="#FFFFFF", ior=1.45, roughness=0.0, screen_refraction=True,
                 cast_shadows=True, shadow_mode=None):
        super().__init__("refraction")
        self.reset()
        self.bsdf = self.create_refraction_bsdf(ior=ior, roughness=roughness)
        self.bsdf["Color"] = color
        self.bsdf["BSDF"].to(self.output["Surface"])
        self.mat.use_screen_refraction = screen_refraction
        self.set_shadows(cast_shadows, shadow_mode)


RefractionBSDF = RefractionMaterial


class VolumeMaterial(NodeMaterial):
    """A Principled Volume material, for fog, smoke or god rays.

    Assign it to a closed mesh (a big cube around the scene for instance) and enable
    ``Scene.add_volumetric_light`` when rendering with Eevee.
    """

    def __init__(self, color="#FFFFFF", density=1.0, emission_strength=0.0, emission_color=None,
                 anisotropy=0.0, cast_shadows=True, shadow_mode=None):
        super().__init__("volume")
        self.reset()
        self.bsdf = self.volume = self.create_volume_principled()
        self.volume["Volume"].to(self.output["Volume"])
        self.volume["Color"] = color
        self.volume["Density"] = density
        self.volume["Anisotropy"] = anisotropy
        if emission_strength > 0:
            self.volume["Emission Color"] = emission_color or color
            self.volume["Emission Strength"] = emission_strength
        self.set_shadows(cast_shadows, shadow_mode)
