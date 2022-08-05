import bpy

from .utils import hex_to_rgb, hex_to_rgba, random_string


def create_glow_material(color, emission_strength=1):
    color = hex_to_rgb(color)

    mat = bpy.data.materials.new(name='Material')
    mat.use_nodes = True

    mat_nodes = mat.node_tree.nodes
    mat_nodes.clear()
    diffuse = mat_nodes.new("ShaderNodeEmission")
    inputs = mat.node_tree.nodes["Emission"].inputs
    inputs["Color"].default_value = (
        color[0], color[1], color[2], 1)
    inputs["Strength"].default_value = emission_strength
    output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")

    links = mat.node_tree.links
    links.new(
        diffuse.outputs[0],
        output.inputs[0])
    return mat


class NodeMaterial:
    def __init__(self, name="NodeMaterial"):
        self.mat = bpy.data.materials.new(name=random_string(10))
        self.mat.use_nodes = True
        self.nodes = self.mat.node_tree.nodes
        self.links = self.mat.node_tree.links
        self.material_output = Node(self.nodes.get("Material Output"), self)
        self.bsdf = Node(self.nodes.get("Principled BSDF"), self)

    def reset(self):
        for node in self.nodes:
            self.nodes.remove(node)

    def create_principled_bsdf(self):
        node = self.mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
        return Node(node, self)

    def create_transparent_bsdf(self):
        node = self.mat.node_tree.nodes.new("ShaderNodeBsdfTransparent")
        return Node(node, self)

    def create_volume_scatter(self):
        node = self.mat.node_tree.nodes.new("ShaderNodeVolumeScatter")
        return Node(node, self)

    def create_normal_map(self, tex=None, strength=10):
        node = self.mat.node_tree.nodes.new("ShaderNodeNormalMap")
        node.inputs["Strength"].default_value = strength
        node = Node(node, self)
        if tex is not None:
            tex["Color"].to(node["Color"])
        return node

    def create_hue_saturation(self, hue=.5, saturation=1., value=1., fac=1.):
        node = self.mat.node_tree.nodes.new("ShaderNodeHueSaturation")
        node = Node(node, self)
        node["Hue"] = hue
        node["Saturation"] = saturation
        node["Value"] = value
        node["Fac"] = fac
        return node

    def create_bevel(self, value=1):
        node = self.mat.node_tree.nodes.new("ShaderNodeBevel")
        node.operation = "MULTIPLY"
        node.inputs[1].default_value = value
        return Node(node, self)

    def create_displacement(self, scale=1., midlevel=1):
        node = self.mat.node_tree.nodes.new("ShaderNodeDisplacement")
        node.inputs["Scale"].default_value = scale
        node.inputs["Midlevel"].default_value = midlevel
        return Node(node, self)

    def create_texture_coordinate(self, use_mapping=True):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexCoord")
        node = Node(node, self)
        if use_mapping:
            mapping = self.create_mapping()
            node["Generated"].to(mapping["Vector"])
        return node, mapping

    def create_mix_shader(self, fac=.5):
        node = self.mat.node_tree.nodes.new("ShaderNodeMixShader")
        node.inputs["Fac"].default_value = fac
        return Node(node, self)

    def create_mix_rgb(self, fac=.5, blend_type="MIX"):
        node = self.mat.node_tree.nodes.new("ShaderNodeMixRGB")
        node.inputs["Fac"].default_value = fac
        node.blend_type = blend_type
        return Node(node, self)

    def create_layer_weight(self, blend=.5):
        node = self.mat.node_tree.nodes.new("ShaderNodeLayerWeight")
        node.inputs["Blend"].default_value = blend
        return Node(node, self)

    def create_emission(self, strength=50, color="#FF0000"):
        node = self.mat.node_tree.nodes.new("ShaderNodeEmission")
        node.inputs["Strength"].default_value = strength
        node.inputs["Color"].default_value = hex_to_rgba(color)
        return Node(node, self)

    def create_mapping(self):
        node = self.mat.node_tree.nodes.new("ShaderNodeMapping")
        return Node(node, self)

    def create_geometry(self):
        node = self.mat.node_tree.nodes.new("ShaderNodeNewGeometry")
        return Node(node, self)

    def create_bump(self, strength=1.):
        node = self.mat.node_tree.nodes.new("ShaderNodeBump")
        node.inputs["Strength"].default_value = strength
        return Node(node, self)

    def create_texture(
        self, image,
        rotation=(0, 0, 0),
        scale=(1, 1, 1),
        frame_offset=0,
        projection="FLAT"
    ):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = image.img
        node.projection = projection
        node.texture_mapping.rotation = rotation
        node.texture_mapping.scale = scale
        node.image_user.frame_offset = frame_offset
        return Node(node, self)

    def create_gradient_texture(self, gradient_type="LINEAR"):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexGradient")
        node.gradient_type = gradient_type
        return Node(node, self)

    def create_checker_texture(self, scale=5):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexChecker")
        node.inputs["Scale"].default_value = scale
        return Node(node, self)

    def create_brick_texture(self, scale=5):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexBrick")
        node.inputs["Scale"].default_value = scale
        return Node(node, self)

    def create_voronoi_texture(self, distance="EUCLIDEAN", scale=5):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexVoronoi")
        node.inputs["Scale"].default_value = scale
        node.distance = distance
        return Node(node, self)

    def create_wave_texture(
        self,
        scale=5, distortion=1, detail=2, detail_scale=1,
        detail_roughness=0.5, phase_offset=0, rings_direction="X",
        wave_type="BANDS", wave_profile="SIN"
    ):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexWave")
        node.wave_type = wave_type
        node.wave_profile = wave_profile
        node.rings_direction = rings_direction
        node.inputs["Scale"].default_value = scale
        node.inputs["Distortion"].default_value = distortion
        node.inputs["Detail"].default_value = detail
        node.inputs["Detail Scale"].default_value = detail_scale
        node.inputs["Detail Roughness"].default_value = detail_roughness
        node.inputs["Phase Offset"].default_value = phase_offset
        return Node(node, self)

    def create_magic_texture(self, scale=5, distortion=1):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexMagic")
        node.inputs["Scale"].default_value = scale
        node.inputs["Distortion"].default_value = distortion
        return Node(node, self)

    def create_musgrave_texture(
        self, scale=5, detail=2, dimension=2, lacunarity=2,
        musgrave_type="MULTIFRACTAL", offset=0, gain=1,
        noise_dimensions="3D"
    ):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexMusgrave")
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
        node.inputs["Dimension"].default_value = dimension
        node.inputs["Lacunarity"].default_value = lacunarity
        node.inputs["Offset"].default_value = offset
        node.inputs["Gain"].default_value = gain
        node.musgrave_type = musgrave_type
        node.musgrave_dimensions = noise_dimensions
        return Node(node, self)

    def create_noise_texture(
        self, color=None, scale=5, detail=2, distortion=0, noise_dimensions="3D", roughness=.5
    ):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexNoise")
        if color is not None:
            color = hex_to_rgb(color)
            node.use_custom_color = True
            node.color = color
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
        node.inputs["Distortion"].default_value = distortion
        node.inputs["Roughness"].default_value = roughness
        node.noise_dimensions = noise_dimensions
        return Node(node, self)

    def create_operation(self, operation="MULTIPLY", value=5):
        node = self.mat.node_tree.nodes.new("ShaderNodeMath")
        node.operation = operation
        node.inputs[1].default_value = value
        return Node(node, self)

    def create_map_range(self, source=[0, 1], target=[0, 1]):
        node = self.mat.node_tree.nodes.new("ShaderNodeMapRange")
        node.inputs[1].default_value = source[0]
        node.inputs[2].default_value = source[1]
        node.inputs[3].default_value = target[0]
        node.inputs[4].default_value = target[1]
        return Node(node, self)

    def create_color_ramp(
        self,
        color_mode="RGB",
        colors=None,
        positions=None,
        interpolation="LINEAR"
    ):
        node = self.mat.node_tree.nodes.new("ShaderNodeValToRGB")
        node.color_ramp.color_mode = color_mode
        node.color_ramp.interpolation = interpolation

        if colors is not None:
            colors = [hex_to_rgba(c) for c in colors]
            if len(colors) > 2:
                for i in range(len(colors) - 2):
                    node.color_ramp.elements.new(.2)
            for i in range(len(colors)):
                node.color_ramp.elements[i].color = colors[i]
        if positions is not None:
            if colors is not None:
                assert len(positions) == len(colors)
            for i in range(len(positions)):
                node.color_ramp.elements[i].position = positions[i]
        return Node(node, self)

    def get_node(self, name):
        if isinstance(name, str):
            name = self.nodes.get(name)
        elif hasattr(name, "_node"):
            name = name._node
        return name

    def link(
            self, source, target="Principled BSDF",
            output="Color", input="Base Color"
    ):
        source = self.get_node(source)
        target = self.get_node(target)
        self.links.new(target.inputs[input], source.outputs[output])


class Node:
    def __init__(self, node, mat):
        self._node = node
        self._mat = mat
        self._current = None

    def link_to(self, target, output="Color", input="Base Color"):
        self._mat.link(self, target, output, input)

    def animate(self, key, values, frames=None, interpolation="LINEAR"):
        path = self._node.inputs[key]
        frames = range(len(values)) if frames is None else frames
        for frame, value in zip(frames, values):
            path.default_value = value
            path.keyframe_insert(data_path="default_value", frame=frame)
            # kf.interpolation = interpolation

    def __setitem__(self, key, value):
        self._node.inputs[key].default_value = value

    def __getitem__(self, key):
        self._current = key
        return self

    def to(self, target):
        self._mat.link(self, target, self._current, target._current)
        target._current = None
        self._current = None

    def unlink(self):
        # for node in self._mat.nodes:
        for socket in self._node.inputs:
            if self._current is None:
                for link in socket.links:
                    self._mat.links.remove(link)
            elif self._current == socket.name:
                for link in socket.links:
                    self._mat.links.remove(link)


class Material(NodeMaterial):
    def __init__(
        self,
        color="#FFFFFF",
        roughness=.5,
        metallic=.5,
        specular=0,
        emission_strength=0,
        emission_color=None,
        transmission=0,
        texture=None,
        cast_shadows=True,
        blend_mode="OPAQUE",
        shadow_mode=None,
        displace=False
    ):
        super().__init__()

        inputs = self.nodes["Principled BSDF"].inputs

        # PBR
        color = hex_to_rgb(color)
        inputs['Base Color'].default_value = (
            color[0], color[1], color[2], 1)
        inputs['Roughness'].default_value = roughness
        inputs['Metallic'].default_value = metallic
        inputs['Specular'].default_value = specular
        inputs['Transmission'].default_value = transmission

        self.mat.blend_method = blend_mode

        if displace:
            self.mat.cycles.displacement_method = "DISPLACEMENT"

        if shadow_mode is not None:
            self.mat.shadow_method = shadow_mode
        elif not cast_shadows:
            self.mat.shadow_method = "NONE"

        if emission_strength > 0:
            if emission_color is None:
                inputs['Emission'].default_value = (
                    color[0], color[1], color[2], 1)
            else:
                ec = hex_to_rgb(emission_color)
                inputs['Emission'].default_value = (
                    ec[0], ec[1], ec[2], 1)
            inputs['Emission Strength'].default_value = emission_strength

        if texture is not None:
            texImage = self.mat.node_tree.nodes.new('ShaderNodeTexImage')
            texImage.image = texture.img
            self.mat.node_tree.links.new(
                inputs["Base Color"], texImage.outputs["Color"])


class VolumeMaterial(NodeMaterial):
    def __init__(
        self,
        color="#FFFFFF",
        emission=0,
        density=1
    ):
        super().__init__()
        self.reset()

        color = hex_to_rgb(color)

        output_node = self.nodes.new(type='ShaderNodeOutputMaterial')
        principled_node = self.nodes.new(type='ShaderNodeVolumePrincipled')
        self.links.new(principled_node.outputs[0],
                       output_node.inputs['Volume'])

        principled_node.color = color
        self.mat.node_tree.nodes.active = principled_node
        inputs = principled_node.inputs
        inputs['Color'].default_value = (
            color[0], color[1], color[2], 1)
        inputs['Density'].default_value = density

        if emission > 0:
            inputs['Emission Strength'].default_value = emission


class EmissionMaterial(NodeMaterial):
    def __init__(
        self,
        color="#FFFFFF",
        emission_strength=1
    ):
        super().__init__()
        self.reset()

        color = hex_to_rgb(color)

        output_node = self.nodes.new(type='ShaderNodeOutputMaterial')
        node = self.nodes.new(type='ShaderNodeEmission')
        self.links.new(node.outputs[0],
                       output_node.inputs['Surface'])

        node.color = color
        self.mat.node_tree.nodes.active = node
        inputs = node.inputs
        inputs['Color'].default_value = (
            color[0], color[1], color[2], 1)
        inputs['Strength'].default_value = emission_strength


class RefractionBSDF(NodeMaterial):
    def __init__(
        self,
        color="#FFFFFF",
        ior=1.45,
        roughness=0.5,
        use_screen_refraction=True
    ):
        super().__init__()
        self.reset()
        self.mat.use_screen_refraction = use_screen_refraction

        color = hex_to_rgb(color)

        node = self.nodes.new(type='ShaderNodeBsdfRefraction')
        output_node = self.nodes.new(type='ShaderNodeOutputMaterial')

        node.color = color
        self.mat.node_tree.nodes.active = node
        inputs = node.inputs
        inputs['Color'].default_value = (color[0], color[1], color[2], 1)
        inputs['IOR'].default_value = ior
        inputs['Roughness'].default_value = roughness
        self.links.new(node.outputs[0], output_node.inputs[0])
        self.bsdf = Node(self.nodes.get("Refraction BSDF"), self)
        self.material_output = Node(self.nodes.get("Material Output"), self)
