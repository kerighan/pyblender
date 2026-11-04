"""Common wrapper for Blender node trees: shader materials, geometry nodes and the compositor.

Sockets are reached as attributes (``noise.fac``, ``bsdf.base_color``) or by name
(``bsdf["Base Color"]``), ``>>`` links them, arithmetic builds Math nodes::

    noise = mat.create_noise_texture(scale=4)
    ramp = mat.create_color_ramp(colors=["#000000", "#FFFFFF"])
    noise.fac >> ramp.fac >> mat.bsdf.base_color      # link a chain
    (noise.fac * 0.1 + 0.05) >> mat.output.displacement   # Math nodes created on the fly
    mat.bsdf.roughness = 0.3                          # set a socket value
    mat.bsdf.roughness.animate([0, 1], [0, 30])       # keyframe it

Without an explicit socket, ``>>`` uses the first output and the first input, so
``noise >> ramp >> bsdf`` works for the common case. ``a.to(b)`` is the same as ``a >> b``.
"""

import numpy as np

from .animation.easing import EASINGS
from .timing import to_frames
from .utils import to_rgba

_PRIVATE = {"node", "tree"}


def _normalize(name):
    return str(name).replace("_", " ").replace("-", " ").lower()


def _coerce(socket, value):
    """Adapt ``value`` to the socket: hex strings and RGB triples for color sockets,
    hex strings for vector sockets."""
    if socket.type == "RGBA":
        return to_rgba(value)
    if socket.type == "VECTOR" and isinstance(value, str):
        return to_rgba(value)[:3]
    return value


class Node:
    """A node of a :class:`NodeTree`.

    ``node["Socket"]`` or ``node.socket_name`` selects a socket (for ``>>``, ``=`` or
    ``animate``); the selection is consumed by the next operation.
    """

    def __init__(self, node, tree):
        object.__setattr__(self, "node", node)
        object.__setattr__(self, "tree", tree)
        object.__setattr__(self, "_socket", None)
        object.__setattr__(self, "_cursor", 0)

    # ------------------------------------------------------------------
    # Socket access
    # ------------------------------------------------------------------

    @property
    def inputs(self):
        return self.node.inputs

    @property
    def outputs(self):
        return self.node.outputs

    def _find(self, collection, name):
        if isinstance(name, int):
            return collection[name]
        if name in collection:
            return collection[name]
        wanted = _normalize(name)
        for socket in collection:
            if _normalize(socket.name) == wanted or _normalize(socket.identifier) == wanted:
                return socket
        return None

    def input(self, name):
        socket = self._find(self.node.inputs, name)
        if socket is None:
            raise KeyError(f"{self.node.name} has no input {name!r}")
        return socket

    def output(self, name):
        socket = self._find(self.node.outputs, name)
        if socket is None:
            raise KeyError(f"{self.node.name} has no output {name!r}")
        return socket

    def __getitem__(self, socket):
        object.__setattr__(self, "_socket", socket)
        return self

    def __getattr__(self, name):
        # only reached when normal attribute lookup fails: treat it as a socket name
        if name.startswith("_"):
            raise AttributeError(name)
        if (self._find(self.node.inputs, name) is None
                and self._find(self.node.outputs, name) is None):
            raise AttributeError(f"{self.node.name} has no socket {name!r}")
        return self[name]

    def __setattr__(self, name, value):
        if name in _PRIVATE or name.startswith("_") or name in type(self).__dict__:
            object.__setattr__(self, name, value)
        else:
            self.set(name, value)

    def __setitem__(self, socket, value):
        self.set(socket, value)

    def set(self, socket=None, value=None, **sockets):
        """Set input sockets: ``node.set("Roughness", 0.3)`` or ``node.set(roughness=0.3)``.
        Colors accept hex strings or RGB(A) tuples."""
        if socket is not None:
            sockets[socket] = value
        for name, val in sockets.items():
            target = self.input(name)
            target.default_value = _coerce(target, val)
        return self

    # ------------------------------------------------------------------
    # Linking
    # ------------------------------------------------------------------

    def _take(self):
        socket = self._socket
        object.__setattr__(self, "_socket", None)
        return socket

    def to(self, target, duration=0.6, easing="cubic-out", start=None):
        """With a node: link the selected output to its selected input (same as ``>>``).
        With a value: tween the selected input socket to it, like objects do::

            noise.fac >> ramp.fac              # link
            mat.bsdf.roughness.to(1, 0.5)      # tween over half a second
        """
        if not isinstance(target, Node):
            return self.tween(target, duration, easing, start)
        output = self._take()
        inp = target._take()
        if target.tree is not self.tree:
            raise ValueError("cannot link nodes that belong to different node trees")
        self.tree.link(self, 0 if output is None else output, target, 0 if inp is None else inp)
        return target

    def tween(self, value, duration=0.6, easing="cubic-out", start=None, socket=None):
        """Tween the selected (or named) input socket from its current value to ``value``.
        Times in seconds."""
        socket = self._take() if socket is None else socket
        target = self.input(socket)
        start = self._cursor if start is None else to_frames(start)
        duration = to_frames(duration)
        current = target.default_value
        current = np.asarray(tuple(current) if hasattr(current, "__len__") else current, float)
        value = np.asarray(_coerce(target, value), dtype=float)
        progress = np.asarray(EASINGS[easing](np.linspace(0, 1, duration + 1)), dtype=float)
        if current.ndim:
            values = current + (value - current) * progress[:, None]
        else:
            values = current + (value - current) * progress
        self.animate(socket, values, range(start, start + duration + 1))
        object.__setattr__(self, "_cursor", start + duration)
        return self

    def wait(self, seconds):
        object.__setattr__(self, "_cursor", self._cursor + to_frames(seconds))
        return self

    def __rshift__(self, target):
        return self.to(target)

    def __rlshift__(self, target):
        return self.to(target)

    def __lshift__(self, source):
        source.to(self)
        return self

    def unlink(self, socket=None):
        """Remove the links entering ``socket``, or every input link when ``socket`` is None."""
        socket = self._take() if socket is None else socket
        for inp in self.node.inputs:
            if socket is None or inp == self._find(self.node.inputs, socket):
                for link in list(inp.links):
                    self.tree.links.remove(link)
        return self

    # ------------------------------------------------------------------
    # Arithmetic: ``a * 2``, ``a + b``, ``-a``… create Math nodes
    # ------------------------------------------------------------------

    def _math(self, operation, other, reverse=False):
        node = self.tree.create_math(operation)
        first, second = (other, self) if reverse else (self, other)
        for index, operand in enumerate((first, second)):
            if isinstance(operand, Node):
                operand.to(node[index])
            else:
                node.node.inputs[index].default_value = operand
        return node

    def __add__(self, other):
        return self._math("ADD", other)

    def __radd__(self, other):
        return self._math("ADD", other, reverse=True)

    def __sub__(self, other):
        return self._math("SUBTRACT", other)

    def __rsub__(self, other):
        return self._math("SUBTRACT", other, reverse=True)

    def __mul__(self, other):
        return self._math("MULTIPLY", other)

    def __rmul__(self, other):
        return self._math("MULTIPLY", other, reverse=True)

    def __truediv__(self, other):
        return self._math("DIVIDE", other)

    def __rtruediv__(self, other):
        return self._math("DIVIDE", other, reverse=True)

    def __pow__(self, other):
        return self._math("POWER", other)

    def __neg__(self):
        return self._math("MULTIPLY", -1.0)

    def __abs__(self):
        node = self.tree.create_math("ABSOLUTE")
        self.to(node[0])
        return node

    def apply(self, operation, value=None):
        """A Math operation on this socket: ``.apply("SINE")``, ``.apply("GREATER_THAN", 0.5)``."""
        node = self.tree.create_math(operation, value)
        self.to(node[0])
        return node

    def clamp(self, minimum=0.0, maximum=1.0):
        node = self.tree.create_clamp(minimum, maximum)
        self.to(node[0])
        return node

    def map_range(self, source=(0, 1), target=(0, 1)):
        node = self.tree.create_map_range(source, target)
        self.to(node[0])
        return node

    def mix(self, other, fac=0.5, blend_type="MIX"):
        """Mix this color with ``other`` (a node or a color) with a MixRGB node."""
        node = self.tree.create_mix_rgb(blend_type, fac)
        self.to(node[1])
        if isinstance(other, Node):
            other.to(node[2])
        else:
            node[2] = other
        return node

    # ------------------------------------------------------------------
    # Keyframes
    # ------------------------------------------------------------------

    def animate(self, socket, values=None, frames=None):
        """Keyframe an input socket: ``node.animate("Roughness", values, frames)`` or
        ``node.roughness.animate(values, frames)``."""
        if values is None or (isinstance(socket, (list, tuple)) and self._socket is not None):
            socket, values, frames = self._take(), socket, values
        target = self.input(socket)
        if frames is None:
            frames = range(len(values))
        for frame, value in zip(frames, values):
            target.default_value = _coerce(target, value)
            target.keyframe_insert("default_value", frame=frame)
        return self

    def animate_output(self, values, frames=None, socket=0):
        """Keyframe an output socket (``Value`` and ``RGB`` nodes carry their value there)."""
        target = self.output(socket)
        if frames is None:
            frames = range(len(values))
        for frame, value in zip(frames, values):
            target.default_value = value
            target.keyframe_insert("default_value", frame=frame)
        return self

    def animate_property(self, name, values, frames=None):
        """Keyframe a node property (``mix`` of a glare node for instance)."""
        if frames is None:
            frames = range(len(values))
        for frame, value in zip(frames, values):
            setattr(self.node, name, value)
            self.node.keyframe_insert(name, frame=frame)
        return self

    def __repr__(self):
        return f"<Node {self.node.name}>"


class NodeTree:
    """Base of :class:`~pyblender.material.NodeMaterial`, :class:`~pyblender.geometry.Geometry`
    and :class:`~pyblender.post.PostProcess`. Subclasses set ``self.nodes`` and ``self.links``."""

    nodes = None
    links = None

    def create(self, node_type, **properties):
        """Create any node by its ``bpy`` type name and set properties on it."""
        node = self.nodes.new(node_type)
        for key, value in properties.items():
            setattr(node, key, value)
        return Node(node, self)

    def get(self, name):
        """Wrap an existing node by name."""
        return Node(self.nodes[name], self)

    def _raw(self, node):
        if isinstance(node, Node):
            return node.node
        if isinstance(node, str):
            return self.nodes[node]
        return node

    def link(self, source, output, target, inp):
        """Connect ``source.outputs[output]`` to ``target.inputs[inp]`` (names or indices)."""
        source, target = Node(self._raw(source), self), Node(self._raw(target), self)
        self.links.new(source.output(output), target.input(inp))
        return self

    def clear(self):
        self.nodes.clear()
        return self

    # ------------------------------------------------------------------
    # Nodes shared by shader, geometry and compositor trees
    # ------------------------------------------------------------------

    _math = "ShaderNodeMath"
    _vector_math = "ShaderNodeVectorMath"
    _value = "ShaderNodeValue"
    _mix_rgb = "ShaderNodeMixRGB"
    _color_ramp = "ShaderNodeValToRGB"
    _map_range = "ShaderNodeMapRange"
    _clamp = "ShaderNodeClamp"
    _separate_xyz = "ShaderNodeSeparateXYZ"
    _combine_xyz = "ShaderNodeCombineXYZ"
    _rgb = "ShaderNodeRGB"

    def create_math(self, operation="MULTIPLY", value=None, **kw):
        """A Math node. ``value`` sets the second input."""
        node = self.create(self._math, operation=operation, **kw)
        if value is not None:
            node.node.inputs[1].default_value = value
        return node

    create_operation = create_math

    def create_vector_math(self, operation="ADD", value=None):
        node = self.create(self._vector_math, operation=operation)
        if value is not None:
            index = 3 if operation == "SCALE" else 1
            node.node.inputs[index].default_value = value
        return node

    def create_value(self, value=0.5):
        node = self.create(self._value)
        node.node.outputs[0].default_value = value
        return node

    def create_rgb(self, color="#FFFFFF"):
        node = self.create(self._rgb)
        node.node.outputs[0].default_value = to_rgba(color)
        return node

    def create_mix_rgb(self, blend_type="MIX", fac=0.5):
        node = self.create(self._mix_rgb, blend_type=blend_type)
        node.node.inputs["Fac"].default_value = fac
        return node

    def create_color_ramp(self, colors=None, positions=None, interpolation="LINEAR",
                          color_mode="RGB"):
        """A color ramp. ``colors`` are spread evenly unless ``positions`` is given."""
        node = self.create(self._color_ramp)
        ramp = node.node.color_ramp
        ramp.color_mode = color_mode
        ramp.interpolation = interpolation
        if colors:
            while len(ramp.elements) < len(colors):
                ramp.elements.new(0)
            while len(ramp.elements) > len(colors):
                ramp.elements.remove(ramp.elements[-1])
            if positions is None:
                positions = [i / max(len(colors) - 1, 1) for i in range(len(colors))]
            for element, color, position in zip(ramp.elements, colors, positions):
                element.position = position
                element.color = to_rgba(color)
        elif positions:
            for element, position in zip(ramp.elements, positions):
                element.position = position
        return node

    def create_map_range(self, source=(0, 1), target=(0, 1), clamp=True):
        node = self.create(self._map_range, clamp=clamp)
        for index, value in zip((1, 2, 3, 4), (*source, *target)):
            node.node.inputs[index].default_value = value
        return node

    def create_clamp(self, minimum=0.0, maximum=1.0):
        node = self.create(self._clamp)
        node.node.inputs[1].default_value = minimum
        node.node.inputs[2].default_value = maximum
        return node

    def create_separate_xyz(self):
        return self.create(self._separate_xyz)

    def create_combine_xyz(self):
        return self.create(self._combine_xyz)
