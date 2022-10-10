import bpy

from pyblender.utils import random_string


class CompositorNode:
    def __init__(self, node, group):
        self._node = node
        self._group = group
        self._current = None

    def __setitem__(self, key, value):
        self._node.inputs[key].default_value = value

    def __getitem__(self, key):
        self._current = key
        return self

    def to(self, target):
        self._group.link(self, target, self._current, target._current)
        target._current = None
        self._current = None

    def animate(self, key, values, frames=None):
        path = self._node.inputs[key]
        frames = range(len(values)) if frames is None else frames
        for frame, value in zip(frames, values):
            path.default_value = value
            path.keyframe_insert(data_path="default_value", frame=frame)


class Compositor:
    def __init__(self, scene):
        self.scene = scene
        self.scene.render.use_compositing = True
        self.scene.use_nodes = True
        self.nodes = self.scene.node_tree.nodes
        self.links = self.scene.node_tree.links
        self.input = CompositorNode(self.nodes["Render Layers"], self)
        self.output = CompositorNode(self.nodes["Composite"], self)

    def create_lens_distortion(self, distortion=1, dispersion=1):
        node = CompositorNode(
            self.nodes.new(type="CompositorNodeLensdist"), self)
        node["Distort"] = distortion
        node["Dispersion"] = dispersion
        return node

    def create_color_correction(self, saturation=1., gain=1., contrast=1.):
        node = self.nodes.new(type="CompositorNodeColorCorrection")
        node.master_saturation = saturation
        node.master_gain = gain
        node.master_contrast = contrast
        return CompositorNode(node, self)

    def create_glare(
        self, size=8, fade=0, mix=0, quality="HIGH", glare_type="FOG_GLOW"
    ):
        node = self.scene.node_tree.nodes.new(type="CompositorNodeGlare")
        node.glare_type = glare_type
        node.quality = quality
        node.fade = fade
        node.mix = mix
        node.size = size
        return CompositorNode(node, self)

    def create_sun_beams(self, size=0, source=(0., 0.)):
        node = self.scene.node_tree.nodes.new(type="CompositorNodeSunBeams")
        node.ray_length = size
        node.source = source
        node = CompositorNode(node, self)
        return node

    def create_mix_rgb(self, fac=.5, blend_type="MIX"):
        node = self.scene.node_tree.nodes.new(type="CompositorNodeMixRGB")
        node.blend_type = blend_type
        node = CompositorNode(node, self)
        node["Fac"] = fac
        return node

    def link(self, source, target, out, inp):
        source = self.get_node(source)
        target = self.get_node(target)
        self.links.new(source.outputs[out], target.inputs[inp])

    def get_node(self, name):
        if isinstance(name, str):
            name = self.nodes.get(name)
        elif hasattr(name, "_node"):
            name = name._node
        return name
