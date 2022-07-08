import os
import subprocess

import bpy

from .camera import Camera
from .light import PointLight, SpotLight, Sun
from .material import Material, VolumeMaterial
from .mesh import Box, Cube, Grid, Line, Plane, Sphere
from .utils import hex_to_rgb

bpy.ops.wm.read_factory_settings(use_empty=True)


def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


class Scene:
    def __init__(self, camera):
        self.animation = False
        self.camera = camera
        self.scene = bpy.context.scene
        self.scene.camera = camera.obj

    def render(
        self, filename, size=(640, 480), fast=True, use_cuda=True, frame_rate=60, export_folder="render", crf=18
    ):
        if fast:
            self.scene.render.engine = "BLENDER_EEVEE"
        else:
            self.scene.render.engine = "CYCLES"

        if use_cuda:
            prefs = bpy.context.preferences.addons['cycles'].preferences
            prefs.compute_device_type = "CUDA"
            bpy.context.scene.cycles.device = "GPU"
            bpy.context.preferences.addons["cycles"].preferences.get_devices()
            for d in (
                bpy.context.preferences.addons["cycles"].preferences.devices
            ):
                d["use"] = 1

        # manage directory
        directory = os.getcwd()
        if ".mp4" in filename:
            import glob
            if export_folder[-1] != "/":
                export_folder += "/"
            export_folder = os.path.join(directory, export_folder)
            for f in glob.glob(export_folder+"*.png"):
                os.remove(f)
        else:
            export_folder = os.path.join(directory, filename)

        self.scene.render.image_settings.file_format = 'PNG'
        self.scene.render.filepath = export_folder

        self.scene.render.resolution_x = size[0]
        self.scene.render.resolution_y = size[1]
        bpy.ops.render.render(write_still=1, animation=self.animation)

        if ".mp4" in filename:
            cmd = (f'ffmpeg -loglevel panic -y -r {frame_rate} -i '
                   f'"{export_folder}%4d.png" '
                   f'-c:v libx264 -vf "fps=fps={frame_rate}" '
                   f'-force_key_frames expr:gte\(t,n_forced*1\) -crf {crf} '
                   f'-profile main -pix_fmt yuv420p {filename}')
            subprocess.check_output(cmd, shell=True)

    def set_animation_bounds(self, start=0, end=100):
        self.scene.frame_start = start
        self.scene.frame_end = end
        self.animation = True

    def add_bloom(self, intensity=.05, radius=2, threshold=.8):
        self.scene.eevee.bloom_intensity = intensity
        self.scene.eevee.bloom_radius = radius
        self.scene.eevee.bloom_threshold = threshold
        self.scene.eevee.use_bloom = True

    def add_volumetric_light(self, volumetric_shadows=True):
        self.scene.eevee.use_volumetric_lights = True
        self.scene.eevee.use_volumetric_shadows = volumetric_shadows
