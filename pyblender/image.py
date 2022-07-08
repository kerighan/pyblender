import bpy


class Image:
    def __init__(self, src):
        self.img = bpy.data.images.load(src, check_existing=False)
