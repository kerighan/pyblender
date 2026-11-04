import bpy

from .utils import to_rgba


class Node:
    """A node of a :class:`NodeMaterial` shader tree."""

    def __init__(self, node):
        self.node = node

    @property
    def inputs(self):
        return self.node.inputs

    @property
    def outputs(self):
        return self.node.outputs


class NodeMaterial:
    """A node-based material. Starts with a Principled BSDF wired to the output."""

    def __init__(self, name="material"):
        self.mat = bpy.data.materials.new(name=name)
        self.mat.use_nodes = True
        self.nodes = self.mat.node_tree.nodes
        self.links = self.mat.node_tree.links
        self.bsdf = Node(self.nodes["Principled BSDF"])
        self.output = Node(self.nodes["Material Output"])

    def add_node(self, node_type, **attributes):
        """Create a node, e.g. ``add_node("ShaderNodeTexNoise", noise_dimensions="4D")``."""
        node = self.nodes.new(node_type)
        for key, value in attributes.items():
            setattr(node, key, value)
        return Node(node)

    def add_math(self, operation="MULTIPLY", value=1.0):
        node = self.add_node("ShaderNodeMath", operation=operation)
        node.inputs[1].default_value = value
        return node

    def add_color_ramp(self, colors=None, color_mode="RGB"):
        """Create a color ramp. ``colors`` is a list of colors spread evenly on the ramp."""
        node = self.add_node("ShaderNodeValToRGB")
        ramp = node.node.color_ramp
        ramp.color_mode = color_mode
        if colors:
            while len(ramp.elements) < len(colors):
                ramp.elements.new(0)
            while len(ramp.elements) > len(colors):
                ramp.elements.remove(ramp.elements[-1])
            for i, (element, color) in enumerate(zip(ramp.elements, colors)):
                element.position = i / max(len(colors) - 1, 1)
                element.color = to_rgba(color)
        return node

    def add_noise_texture(self, scale=5.0, detail=2.0, roughness=0.5):
        node = self.add_node("ShaderNodeTexNoise")
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
        node.inputs["Roughness"].default_value = roughness
        return node

    def add_image_texture(self, image):
        node = self.add_node("ShaderNodeTexImage")
        node.node.image = image.img
        return node

    def link(self, source, target, output=0, input=0):
        """Connect ``source.outputs[output]`` to ``target.inputs[input]``.

        Sockets can be given by name or index.
        """
        self.links.new(source.outputs[output], target.inputs[input])
        return self


class Material(NodeMaterial):
    """A Principled BSDF material.

    Arguments:
        color: base color as a hex string or ``(r, g, b)`` floats.
        roughness, metallic, specular: PBR parameters in [0, 1].
        opacity: 1 is fully opaque, lower values make the material transmissive.
        emission_strength: makes the material glow (combine with ``Scene.add_bloom``).
        emission_color: hex string, defaults to ``color``.
        texture: an :class:`~pyblender.image.Image` used as base color.
        cast_shadows: disable to make the object invisible to shadows.
    """

    def __init__(
        self,
        color="#FFFFFF",
        roughness=0.5,
        metallic=0.5,
        specular=0.0,
        opacity=1.0,
        emission_strength=0.0,
        emission_color=None,
        texture=None,
        cast_shadows=True,
    ):
        super().__init__()
        inputs = self.bsdf.inputs

        inputs["Base Color"].default_value = to_rgba(color)
        inputs["Roughness"].default_value = roughness
        inputs["Metallic"].default_value = metallic
        inputs["Specular"].default_value = specular

        if opacity != 1:
            inputs["Transmission"].default_value = 1
            inputs["Alpha"].default_value = opacity
            self.mat.blend_method = "BLEND"

        if not cast_shadows:
            self.mat.shadow_method = "NONE"

        if emission_strength > 0:
            inputs["Emission"].default_value = to_rgba(emission_color or color, opacity)
            inputs["Emission Strength"].default_value = emission_strength

        if texture is not None:
            self.link(self.add_image_texture(texture), self.bsdf, "Color", "Base Color")

    def animate_color(self, values, frames=None):
        """Keyframe the base color from a list of colors."""
        if frames is None:
            frames = range(len(values))
        socket = self.bsdf.inputs["Base Color"]
        for frame, color in zip(frames, values):
            socket.default_value = to_rgba(color)
            socket.keyframe_insert("default_value", frame=frame)
        return self


class VolumeMaterial:
    """A Principled Volume material, for fog, smoke or god rays.

    Assign it to a closed mesh (a big cube around the scene for instance)
    and enable ``Scene.add_volumetric_light`` when rendering with Eevee.
    """

    def __init__(self, color="#FFFFFF", density=1.0, emission_strength=0.0, emission_color=None):
        self.mat = bpy.data.materials.new(name="volume")
        self.mat.use_nodes = True
        nodes = self.mat.node_tree.nodes
        nodes.clear()

        output = nodes.new("ShaderNodeOutputMaterial")
        volume = nodes.new("ShaderNodeVolumePrincipled")
        self.mat.node_tree.links.new(volume.outputs["Volume"], output.inputs["Volume"])

        volume.inputs["Color"].default_value = to_rgba(color)
        volume.inputs["Density"].default_value = density
        if emission_strength > 0:
            volume.inputs["Emission Color"].default_value = to_rgba(emission_color or color)
            volume.inputs["Emission Strength"].default_value = emission_strength
        self.volume = Node(volume)
