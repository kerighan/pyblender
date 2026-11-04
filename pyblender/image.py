import bpy


class Image:
    """An image datablock loaded from disk, usable as texture or displacement map."""

    def __init__(self, path):
        self.img = bpy.data.images.load(path, check_existing=True)
