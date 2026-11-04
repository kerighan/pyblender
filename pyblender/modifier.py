import bpy


class Displacement:
    """Displace the vertices of ``mesh`` along their normals using ``image`` as a height map.

    The mesh needs enough vertices for the effect to show: use a :class:`~pyblender.mesh.Grid`
    with many subdivisions or add a :class:`Subdivision` first.
    """

    def __init__(self, mesh, image, strength=1.0, midlevel=0.5):
        name = f"displace_{mesh.obj.name}"
        texture = bpy.data.textures.new(name, "IMAGE")
        texture.image = image.img

        self.modifier = mesh.obj.modifiers.new(name, "DISPLACE")
        self.modifier.texture = texture
        self.modifier.strength = strength
        self.modifier.mid_level = midlevel


class Subdivision:
    """Subdivision surface modifier. ``levels`` applies at render time."""

    def __init__(self, mesh, levels=2, smooth=True):
        self.modifier = mesh.obj.modifiers.new("subdivision", "SUBSURF")
        self.modifier.render_levels = levels
        self.modifier.levels = levels
        self.modifier.subdivision_type = "CATMULL_CLARK" if smooth else "SIMPLE"
