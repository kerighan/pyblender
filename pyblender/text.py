"""3D text, as a single object or split into letters or words for per-part animation."""

import bpy

from .base import BlenderObject, Empty, Group, link_to_scene
from .mesh import Mesh, as_material
from .utils import to_radians

UPRIGHT = (90, 0, 0)  # text standing in the XZ plane, readable from -Y


def load_font(path):
    """Load a ``.ttf`` / ``.otf`` file, or return Blender's built-in font when ``path`` is None."""
    if path is None:
        return bpy.data.fonts["Bfont"] if "Bfont" in bpy.data.fonts else None
    return bpy.data.fonts.load(path, check_existing=True)


class TextObject(Mesh):
    """A single text curve object. Use :class:`Text`, which also handles splitting."""

    def __init__(self, body, size=1.0, extrude=0.0, bevel=0.0, font=None, material=None,
                 location=(0, 0, 0), rotation=(0, 0, 0), align="center", tracking=0.0,
                 line_spacing=1.0, visible=True, name="text"):
        curve = bpy.data.curves.new(name, type="FONT")
        curve.body = body
        curve.size = size
        curve.extrude = extrude
        curve.bevel_depth = bevel
        curve.bevel_resolution = 2 if bevel else 0
        curve.align_x = align.upper()
        curve.align_y = "BOTTOM_BASELINE"
        curve.space_character = 1.0 + tracking
        curve.space_line = line_spacing
        if font is not None:
            curve.font = font

        self.curve = curve
        self.obj = link_to_scene(bpy.data.objects.new(name, curve))
        self.obj.location = location
        self.obj.rotation_euler = to_radians(rotation)
        self._setup(material, visible)

    @property
    def body(self):
        return self.curve.body

    @body.setter
    def body(self, value):
        self.curve.body = value

    @property
    def width(self):
        """Rendered width, computed on demand (triggers a scene update)."""
        bpy.context.view_layer.update()
        return self.obj.dimensions.x


class Text(BlenderObject):
    """3D text.

    Arguments:
        body: the string to display, ``\\n`` starts a new line.
        size: letter height in scene units.
        extrude: depth of the 3D extrusion.
        bevel: rounding of the edges.
        font: path to a ``.ttf``/``.otf`` file, defaults to Blender's built-in font.
        material: a :class:`~pyblender.material.Material`.
        location, rotation: placement of the whole text (degrees). The origin is at the baseline.
        upright: when ``rotation`` is not given, stand the text up so it faces a camera
            placed on -Y (``rotation=(90, 0, 0)`` degrees). Otherwise the text lies flat on XY.
        align: ``"left"``, ``"center"`` or ``"right"``, relative to the origin.
        tracking: extra spacing between letters, as a fraction of ``size``.
        split: ``None`` for a single object, ``"letters"`` or ``"words"`` to create one object
            per part, all parented to an invisible group. :attr:`parts` is then a
            :class:`~pyblender.base.Group` with the staggered motions
            (``text.parts.pop_in(stagger=3)``).

    Tweens and ``animate_*`` on the text itself move the whole group, so a text can be
    animated as a block while its letters are animated individually.
    """

    def __init__(self, body, size=1.0, extrude=0.0, bevel=0.0, font=None, material=None,
                 location=(0, 0, 0), rotation=None, upright=True, align="center", tracking=0.0,
                 line_spacing=1.0, split=None, visible=True):
        if rotation is None:
            rotation = UPRIGHT if upright else (0, 0, 0)
        material = as_material(material)
        font = load_font(font) if isinstance(font, str) or font is None else font
        self.body = body
        self.size = size
        self.split = split
        style = dict(size=size, extrude=extrude, bevel=bevel, font=font, material=material,
                     tracking=tracking, line_spacing=line_spacing, visible=visible)

        if split is None:
            whole = TextObject(body, location=location, rotation=rotation, align=align, **style)
            self.obj = whole.obj
            self.parts = Group([whole])
            return

        if "\n" in body:
            raise ValueError("split text supports a single line")
        group = Empty(location, name="text")
        group.obj.rotation_euler = to_radians(rotation)
        group.set_visible(visible)
        self.obj = group.obj
        self.parts = self._build_parts(body, align, **style)

    # ------------------------------------------------------------------

    def _build_parts(self, body, align, size, tracking, **style):
        if self.split == "letters":
            tokens = list(body)
        elif self.split == "words":
            tokens = body.split(" ")
            tokens = [t for token in tokens for t in (token, " ")][:-1]
        else:
            raise ValueError(f"split must be None, 'letters' or 'words', got {self.split!r}")

        parts = [
            None if token == " " else TextObject(token, size=size, tracking=tracking,
                                                 align="center", name=f"text_{i}", **style)
            for i, token in enumerate(tokens)
        ]
        for part in parts:
            if part is not None:
                part.obj.parent = self.obj

        bpy.context.view_layer.update()
        space = _space_width(style["font"], size)
        widths = [space if part is None else part.obj.dimensions.x for part in parts]
        gap = tracking * size
        total = sum(widths) + gap * (len(parts) - 1)
        cursor = {"left": 0.0, "center": -total / 2, "right": -total}[align]
        for part, width in zip(parts, widths):
            if part is not None:
                part.obj.location = (cursor + width / 2, 0, 0)
            cursor += width + gap
        self.width = total
        return Group(part for part in parts if part is not None)

    def __iter__(self):
        return iter(self.parts)

    def __len__(self):
        return len(self.parts)

    def set_material(self, material):
        for part in self.parts:
            part.set_material(material)
        return self


def _space_width(font, size):
    """Width of a space: measured as the difference between "a a" and "aa"."""
    widths = []
    for body in ("a a", "aa"):
        probe = TextObject(body, size=size, font=font, align="left", name="probe")
        widths.append(probe.width)
        bpy.data.objects.remove(probe.obj)
        bpy.data.curves.remove(probe.curve)
    return max(widths[0] - widths[1], 0.2 * size)
