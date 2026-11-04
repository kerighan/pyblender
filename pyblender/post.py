"""Post-processing effects on the rendered image, built on Blender's compositor.

Effects are stacked in the order they are added and every parameter can be animated
with the usual ``(values, frames)`` convention::

    post = scene.post
    post.vignette(0.4)
    post.scanlines(0.15)
    glow = post.glow(threshold=1.0, mix=0.3)
    split = post.rgb_split()
    split.animate("x", [0, 12, 0], [40, 45, 50])     # pixels
    post.glitch(bursts=[(40, 52), (90, 96)])          # sci-fi screen glitch preset
"""

import bpy
import numpy as np

__all__ = ["PostProcess", "Effect"]


class Effect:
    """One effect of the stack. ``params`` maps a name to the Blender properties it drives."""

    def __init__(self, name, params):
        self.name = name
        # name -> list of (owner, property, index, transform); transform maps the
        # user value to the Blender value (index -1 means a scalar property)
        self.params = params

    def _apply(self, name, value, frame=None):
        for owner, prop, index, transform in self.params[name]:
            if index < 0:
                setattr(owner, prop, transform(value))
            else:
                getattr(owner, prop)[index] = transform(value)
            if frame is not None:
                owner.keyframe_insert(prop, index=index, frame=frame)

    def set(self, name, value):
        self._apply(name, value)
        return self

    def animate(self, name, values, frames=None):
        """Keyframe parameter ``name``: one value per frame."""
        if frames is None:
            frames = range(len(values))
        for frame, value in zip(frames, values):
            self._apply(name, value, frame)
        return self

    def burst(self, name, bursts, low=0.0, high=1.0, seed=0, rest=0.0):
        """Random values in ``[low, high]`` on every frame of each ``(start, end)`` burst,
        ``rest`` elsewhere."""
        rng = np.random.default_rng(seed)
        values, frames = [], []
        for start, end in bursts:
            frames += [start - 1] + list(range(start, end + 1)) + [end + 1]
            values += [rest] + list(rng.uniform(low, high, end - start + 1)) + [rest]
        return self.animate(name, values, frames)


def _identity(value):
    return value


def _negate(value):
    return -value


def _socket(node, name, transform=_identity):
    return (node.inputs[name], "default_value", -1, transform)


def _prop(node, name, transform=_identity):
    return (node, name, -1, transform)


class PostProcess:
    """A stack of compositor effects applied to the final image. Access it via ``Scene.post``."""

    def __init__(self, scene):
        scene.use_nodes = True
        scene.render.use_compositing = True
        self.tree = scene.node_tree
        self.nodes = self.tree.nodes
        self.links = self.tree.links
        self.nodes.clear()
        self.render_layers = self.nodes.new("CompositorNodeRLayers")
        self.composite = self.nodes.new("CompositorNodeComposite")
        self.output = self.render_layers.outputs["Image"]
        self.links.new(self.output, self.composite.inputs["Image"])
        self.effects = []
        self._textures = 0

    # ------------------------------------------------------------------
    # Plumbing
    # ------------------------------------------------------------------

    def _node(self, node_type, **props):
        node = self.nodes.new(node_type)
        for key, value in props.items():
            setattr(node, key, value)
        return node

    def _chain(self, node, input="Image", output="Image"):
        """Insert ``node`` at the end of the stack."""
        self.links.new(self.output, node.inputs[input])
        self.output = node.outputs[output]
        self.links.new(self.output, self.composite.inputs["Image"])
        return node

    def _register(self, name, params):
        effect = Effect(name, params)
        self.effects.append(effect)
        return effect

    def _texture(self, kind, scale=(1, 1, 1), **props):
        """A compositor Texture node sampling a procedural texture; ``scale`` is per axis."""
        self._textures += 1
        texture = bpy.data.textures.new(f"post_{kind.lower()}_{self._textures}", kind)
        for key, value in props.items():
            setattr(texture, key, value)
        node = self._node("CompositorNodeTexture", texture=texture)
        node.inputs["Scale"].default_value = scale
        return node

    def _mix(self, blend_type, fac, image_b):
        """Mix the current image (A) with ``image_b`` and chain the result."""
        mix = self._node("CompositorNodeMixRGB", blend_type=blend_type)
        mix.inputs["Fac"].default_value = fac
        self.links.new(image_b, mix.inputs[2])
        self._chain(mix, input=1)
        return mix

    # ------------------------------------------------------------------
    # Effects
    # ------------------------------------------------------------------

    def rgb_split(self, x=0.0, y=0.0):
        """Shift the red and blue channels in opposite directions. ``x``, ``y`` in pixels."""
        separate = self._node("CompositorNodeSepRGBA")
        self.links.new(self.output, separate.inputs["Image"])
        red = self._node("CompositorNodeTranslate", wrap_axis="BOTH")
        blue = self._node("CompositorNodeTranslate", wrap_axis="BOTH")
        combine = self._node("CompositorNodeCombRGBA")
        self.links.new(separate.outputs["R"], red.inputs["Image"])
        self.links.new(separate.outputs["B"], blue.inputs["Image"])
        self.links.new(red.outputs["Image"], combine.inputs["R"])
        self.links.new(separate.outputs["G"], combine.inputs["G"])
        self.links.new(blue.outputs["Image"], combine.inputs["B"])
        self.links.new(separate.outputs["A"], combine.inputs["A"])
        self.output = combine.outputs["Image"]
        self.links.new(self.output, self.composite.inputs["Image"])
        effect = self._register("rgb_split", {
            "x": [_socket(red, "X"), _socket(blue, "X", _negate)],
            "y": [_socket(red, "Y"), _socket(blue, "Y", _negate)],
        })
        return effect.set("x", x).set("y", y)

    def chromatic_aberration(self, amount=0.0, distort=0.0):
        """Lens dispersion (color fringes) and barrel distortion, both in [0, 1]."""
        node = self._chain(self._node("CompositorNodeLensdist", use_fit=True))
        effect = self._register("chromatic_aberration", {
            "amount": [_socket(node, "Dispersion")], "distort": [_socket(node, "Distort")]})
        return effect.set("amount", amount).set("distort", distort)

    def slices(self, strength=0.0, coverage=0.3, size=0.15, seed=0):
        """Horizontal bands of the image shifted sideways with wrap-around, the classic glitch.

        ``strength`` is the shift in pixels, ``coverage`` the fraction of the height
        affected, ``size`` the band thickness. Animate ``offset`` to make bands jump.
        """
        bands = self._texture("CLOUDS", scale=(0, 1 / size, 0), noise_scale=1, noise_depth=0)
        bands.inputs["Offset"].default_value = (0, seed * 7.31, 0)
        gate = self._node("CompositorNodeMath", operation="GREATER_THAN")
        gate.inputs[1].default_value = 1 - coverage
        self.links.new(bands.outputs["Value"], gate.inputs[0])

        shifted = self._node("CompositorNodeTranslate", wrap_axis="BOTH")
        self.links.new(self.output, shifted.inputs["Image"])
        mix = self._node("CompositorNodeMixRGB", blend_type="MIX")
        self.links.new(gate.outputs["Value"], mix.inputs["Fac"])
        self.links.new(shifted.outputs["Image"], mix.inputs[2])
        self._chain(mix, input=1)

        effect = self._register("slices", {
            "strength": [_socket(shifted, "X")],
            "coverage": [(gate.inputs[1], "default_value", -1, lambda c: 1 - c)],
            "offset": [(bands.inputs["Offset"], "default_value", 1, _identity)],
        })
        return effect.set("strength", strength)

    def grain(self, amount=0.0):
        """Film grain, new on every frame. ``amount`` in [0, 1]."""
        noise = self._texture("NOISE")
        mix = self._mix("SOFT_LIGHT", amount, noise.outputs["Color"])
        return self._register("grain", {"amount": [_socket(mix, "Fac")]})

    def scanlines(self, amount=0.0, density=200):
        """Horizontal CRT lines. ``density`` is the number of lines over the image height."""
        lines = self._texture("WOOD", scale=(0, density, 0), wood_type="BANDS",
                              noise_basis_2="SIN")
        mix = self._mix("MULTIPLY", amount, lines.outputs["Color"])
        return self._register("scanlines", {"amount": [_socket(mix, "Fac")]})

    def vignette(self, amount=0.0, size=0.9, softness=0.4):
        """Darken the corners. ``size`` is the ellipse diameter relative to the frame."""
        mask = self._node("CompositorNodeEllipseMask", width=size, height=size)
        blur = self._node("CompositorNodeBlur", use_relative=True, factor_x=softness * 100,
                          factor_y=softness * 100, filter_type="FAST_GAUSS")
        self.links.new(mask.outputs["Mask"], blur.inputs["Image"])
        mix = self._mix("MULTIPLY", amount, blur.outputs["Image"])
        return self._register("vignette", {"amount": [_socket(mix, "Fac")]})

    def glow(self, threshold=1.0, mix=0.0, size=7, kind="FOG_GLOW", streaks=4):
        """Compositor glare. ``mix`` in [-1, 1]: -1 original only, 0 balanced, 1 glare only.

        ``kind`` is ``"FOG_GLOW"``, ``"STREAKS"``, ``"GHOSTS"`` or ``"SIMPLE_STAR"``.
        """
        node = self._chain(self._node("CompositorNodeGlare", glare_type=kind, threshold=threshold,
                                      mix=mix, size=size, streaks=streaks, quality="MEDIUM"))
        return self._register("glow", {"mix": [_prop(node, "mix")],
                                       "threshold": [_prop(node, "threshold")]})

    def roll(self, y=0.0, x=0.0):
        """Shift the whole image with wrap-around, like a rolling VHS picture. In pixels."""
        node = self._chain(self._node("CompositorNodeTranslate", wrap_axis="BOTH"))
        effect = self._register("roll", {"x": [_socket(node, "X")], "y": [_socket(node, "Y")]})
        return effect.set("x", x).set("y", y)

    def color(self, hue=0.5, saturation=1.0, value=1.0):
        """Hue rotation (0.5 is neutral), saturation and brightness multipliers."""
        node = self._chain(self._node("CompositorNodeHueSat"))
        effect = self._register("color", {"hue": [_socket(node, "Hue")],
                                          "saturation": [_socket(node, "Saturation")],
                                          "value": [_socket(node, "Value")]})
        return effect.set("hue", hue).set("saturation", saturation).set("value", value)

    def exposure(self, stops=0.0):
        """Exposure in stops, handy for flickers."""
        node = self._chain(self._node("CompositorNodeExposure"))
        effect = self._register("exposure", {"stops": [_socket(node, "Exposure")]})
        return effect.set("stops", stops)

    def blur(self, size=0.0):
        """Gaussian blur, ``size`` relative to the frame width (0.01 is subtle)."""
        node = self._chain(self._node("CompositorNodeBlur", use_relative=True, factor_x=100,
                                      factor_y=100, filter_type="FAST_GAUSS"))
        return self._register("blur", {"size": [_socket(node, "Size")]}).set("size", size)

    def pixelate(self, size=4):
        """Blocky pixels of ``size`` screen pixels. Not animatable."""
        down = self._chain(self._node("CompositorNodeScale", space="RELATIVE"))
        down.inputs["X"].default_value = down.inputs["Y"].default_value = 1 / size
        self._chain(self._node("CompositorNodePixelate"), input="Color", output="Color")
        up = self._chain(self._node("CompositorNodeScale", space="RELATIVE"))
        up.inputs["X"].default_value = up.inputs["Y"].default_value = size
        return self._register("pixelate", {})

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------

    def glitch(self, bursts, strength=1.0, seed=0):
        """Sci-fi screen glitch during each ``(start, end)`` frame range of ``bursts``.

        Random RGB split, sliced displacement, grain and a brightness flicker on every
        frame of a burst, nothing outside. ``strength`` scales the amplitude.
        Returns the effects created, for further tweaking.
        """
        split = self.rgb_split()
        slices = self.slices(size=0.08)
        grain = self.grain()
        flicker = self.exposure()
        split.burst("x", bursts, -25 * strength, 25 * strength, seed=seed)
        slices.burst("strength", bursts, -60 * strength, 60 * strength, seed=seed + 1)
        slices.burst("coverage", bursts, 0.1, 0.5, seed=seed + 2)
        slices.burst("offset", bursts, 0, 100, seed=seed + 3)
        grain.burst("amount", bursts, 0.2 * strength, 0.6 * strength, seed=seed + 4)
        flicker.burst("stops", bursts, -0.3 * strength, 0.4 * strength, seed=seed + 5)
        return [split, slices, grain, flicker]
