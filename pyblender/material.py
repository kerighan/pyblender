import bpy

from .utils import hex_to_rgb, hex_to_rgba


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
        self.mat = bpy.data.materials.new(name=name)
        self.mat.use_nodes = True
        self.nodes = self.mat.node_tree.nodes
        self.links = self.mat.node_tree.links
        self.bsdf = self.nodes.get("Principled BSDF")
        self.material_output = self.nodes.get("Material Output")

    # def create_bevel(self):
    #     node = self.mat.node_tree.nodes.new("ShaderNodeBevel")
    #     node.operation = "MULTIPLY"
    #     node.inputs[1].default_value = value
    #     return Node(node, self)

    def create_math_node(self, operation="MULTIPLY", value=5):
        node = self.mat.node_tree.nodes.new("ShaderNodeMath")
        node.operation = operation
        node.inputs[1].default_value = value
        return Node(node, self)

    def create_color_ramp(self, color_mode="RGB", colors=None):
        node = self.mat.node_tree.nodes.new("ShaderNodeValToRGB")
        node.color_ramp.color_mode = color_mode

        if colors is not None:
            colors = [hex_to_rgba(c) for c in colors]
            for i in range(len(colors)):
                node.color_ramp.elements[i].color = colors[i]
        return Node(node, self)

    def create_noise_texture(self, color=None):
        node = self.mat.node_tree.nodes.new("ShaderNodeTexNoise")
        if color is not None:
            color = hex_to_rgb(color)
            node.use_custom_color = True
            node.color = color
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


class Material(NodeMaterial):
    def __init__(
        self,
        color="#FFFFFF",
        roughness=.5,
        metallic=.5,
        specular=0,
        opacity=1,
        emission_strength=0,
        emission_color=None,
        texture=None,
        cast_shadows=True
    ):
        color = hex_to_rgb(color)

        # mat = bpy.data.materials.new(name='Material')
        # mat.use_nodes = True
        super().__init__()

        inputs = self.nodes["Principled BSDF"].inputs

        # PBR
        inputs['Base Color'].default_value = (
            color[0], color[1], color[2], 1)
        inputs['Roughness'].default_value = roughness
        inputs['Metallic'].default_value = metallic
        inputs['Specular'].default_value = specular

        if opacity != 1:
            inputs['Transmission'].default_value = 1
            inputs['Alpha'].default_value = opacity
            self.mat.blend_method = 'BLEND'

        if not cast_shadows:
            self.mat.shadow_method = "NONE"

        if emission_strength > 0:
            if emission_color is None:
                inputs['Emission'].default_value = (
                    color[0], color[1], color[2], opacity)
            else:
                ec = hex_to_rgb(emission_color)
                inputs['Emission'].default_value = (
                    ec[0], ec[1], ec[2], opacity)
            inputs['Emission Strength'].default_value = emission_strength

        if texture is not None:
            texImage = self.mat.node_tree.nodes.new('ShaderNodeTexImage')
            texImage.image = texture.img
            self.mat.node_tree.links.new(
                inputs["Base Color"], texImage.outputs["Color"])


class VolumeMaterial:
    def __init__(
        self,
        color="#FFFFFF",
        emission=0,
        density=1
    ):
        color = hex_to_rgb(color)

        mat = bpy.data.materials.new(name='Material')
        mat.use_nodes = True
        mat_nodes = mat.node_tree.nodes
        for node in mat_nodes:
            mat_nodes.remove(node)
        links = mat.node_tree.links

        output_node = mat_nodes.new(type='ShaderNodeOutputMaterial')
        principled_node = mat_nodes.new(type='ShaderNodeVolumePrincipled')
        links.new(principled_node.outputs[0],
                  output_node.inputs['Volume'])

        principled_node.color = color
        mat.node_tree.nodes.active = principled_node
        inputs = principled_node.inputs

        # principled_node
        print(inputs)
        inputs['Color'].default_value = (
            color[0], color[1], color[2], 1)
        inputs['Density'].default_value = density

        # if opacity != 1:
        #     inputs['Transmission'].default_value = 1
        #     inputs['Alpha'].default_value = opacity
        #     mat.blend_method = 'BLEND'

        # if not cast_shadows:
        #     mat.shadow_method = "NONE"

        if emission > 0:
            inputs['Emission Strength'].default_value = emission

        self.mat = mat
