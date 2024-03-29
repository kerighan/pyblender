import os
import subprocess

import bpy
import sys

from .camera import Camera
from .light import PointLight, SpotLight, Sun
from .material import Material, VolumeMaterial
from .mesh import Box, Cube, Grid, Line, Plane, Sphere
from .utils import hex_to_rgb, hex_to_rgba

bpy.ops.wm.read_factory_settings(use_empty=True)
if bpy.context.scene.rigidbody_world is None:
    bpy.ops.rigidbody.world_add()
    bpy.context.scene.rigidbody_world.enabled = True

rigid_collection = bpy.data.collections.new("rigid_collection")
bpy.context.scene.rigidbody_world.collection = rigid_collection


dir = os.path.dirname(bpy.data.filepath)
if not dir in sys.path:
    sys.path.append(dir)


def reset():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


class Scene:
    def __init__(
        self,
        size=(640, 480),
        cycles=False,
        samples=64
    ):
        self.animation = False
        self.scene = bpy.context.scene
        self.scene.render.resolution_x = size[0]
        self.scene.render.resolution_y = size[1]

        self.cycles = cycles
        if cycles:
            self.scene.render.engine = "CYCLES"
            bpy.context.scene.cycles.samples = samples
        else:
            self.scene.render.engine = "BLENDER_EEVEE"
            self.scene.eevee.taa_render_samples = samples

    def create_compositor(self):
        from .compositor import Compositor
        comp = Compositor(self.scene)
        return comp

    def render(
        self,
        filename,
        background_color="#000000",
        use_gpu=True,
        use_ssr=True,
        use_ssr_refraction=False,
        use_gtao=True,
        use_motion_blur=False,
        frame_rate=30,
        frame=1,
        exposure=0,
        gamma=1,
        use_volumetric_shadows=False,
        export_folder="render",
        samples=64,
        volumetric_tile_size="8",
        volumetric_samples=64,
        gravity=(0.0, 0.0, -9.81),
        crf=18,
        contrast="Medium High Contrast",
        view_transform="Filmic",
        animation=False,
        bake=True,
        clean_render_directory=False
    ):
        self.scene.gravity = gravity
        self.scene.frame_set(frame)

        if ".mp4" in filename or animation == True:
            animation = True

        if not self.cycles:
            self.scene.eevee.use_ssr = use_ssr
            self.scene.eevee.use_ssr_refraction = use_ssr_refraction
            self.scene.eevee.use_gtao = use_gtao
            self.scene.eevee.use_motion_blur = use_motion_blur
            self.scene.eevee.taa_render_samples = samples
            self.scene.eevee.volumetric_tile_size = volumetric_tile_size
            self.scene.eevee.volumetric_samples = volumetric_samples
            if use_volumetric_shadows:
                self.scene.eevee.use_volumetric_shadows = True
        else:
            if use_motion_blur:
                bpy.context.scene.cycles.rolling_shutter_type = 'TOP'

        if use_gpu:
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
            if os.name == 'nt':
                if export_folder[-1] != "\\":
                    export_folder += "\\"
            else:
                if export_folder[-1] != "/":
                    export_folder += "/"
            export_folder = os.path.join(directory, export_folder)
            if clean_render_directory:
                for f in glob.glob(export_folder+"*.png"):
                    os.remove(f)
        else:
            export_folder = os.path.join(directory, filename)

        # export settings
        self.scene.view_settings.look = contrast
        self.scene.view_settings.view_transform = view_transform
        self.scene.view_settings.exposure = exposure
        self.scene.view_settings.gamma = gamma
        self.scene.render.image_settings.file_format = 'PNG'
        self.scene.render.filepath = export_folder
        self.scene.use_gravity = True

        # set background color
        world = bpy.data.worlds.new("World")
        world.use_nodes = True
        world_nodes = world.node_tree.nodes
        world_nodes['Background'].inputs[0].default_value = hex_to_rgba(
            background_color)
        self.scene.world = world

        if bake:
            bpy.ops.ptcache.bake_all(bake=True)
        # render
        bpy.ops.render.render(write_still=1, animation=animation)
        if ".mp4" in filename:
            if os.name == 'nt':
                cmd = (f'ffmpeg -loglevel panic -y -r {frame_rate} -i '
                       f'"{export_folder}%4d.png" '
                       f'-c:v libx264rgb -crf {crf} '
                       f'{filename}')
            else:
                cmd = (f'ffmpeg -loglevel panic -y -r {frame_rate} -i '
                       f'"{export_folder}%4d.png" '
                       f'-c:v libx264rgb -vf "fps=fps={frame_rate}" '
                       f'-force_key_frames expr:gte\(t,n_forced*1\) -crf {crf} '
                       f'-profile main {filename}')
            subprocess.check_output(cmd, shell=True)

    def set_animation_bounds(self, start=1, end=100):
        self.scene.frame_start = start
        self.scene.frame_end = end

    def add_bloom(self, intensity=.05, radius=2, threshold=.8):
        self.scene.eevee.bloom_intensity = intensity
        self.scene.eevee.bloom_radius = radius
        self.scene.eevee.bloom_threshold = threshold
        self.scene.eevee.use_bloom = True

    def add_glare(
            self,
            size=8,
            mix=0,
            fade=0,
            dispersion=0.01,
            saturation=1.1,
            contrast=1,
            gain=1.1):
        self.scene.render.use_compositing = True
        self.scene.use_nodes = True
        tree = self.scene.node_tree
        nodes = tree.nodes
        links = tree.links

        layers_node = nodes["Render Layers"]
        composite_node = nodes["Composite"]

        color_correction_node = self.scene.node_tree.nodes.new(
            type="CompositorNodeColorCorrection")
        color_correction_node.master_saturation = saturation
        color_correction_node.master_gain = gain
        color_correction_node.master_contrast = contrast

        lens_distortion_node = self.scene.node_tree.nodes.new(
            type="CompositorNodeLensdist")
        lens_distortion_node.inputs["Distort"].default_value = - \
            dispersion * 0.40
        lens_distortion_node.inputs["Dispersion"].default_value = dispersion

        glare_node = self.scene.node_tree.nodes.new(type="CompositorNodeGlare")
        glare_node.glare_type = 'FOG_GLOW'
        glare_node.quality = 'HIGH'
        glare_node.fade = fade
        glare_node.mix = mix
        glare_node.size = size

        # composite_node = self.scene.node_tree.nodes.new(
        #     type="CompositorNodeComposite")
        links.new(layers_node.outputs["Image"],
                  lens_distortion_node.inputs["Image"])
        links.new(lens_distortion_node.outputs["Image"],
                  color_correction_node.inputs["Image"])
        links.new(
            color_correction_node.outputs["Image"], glare_node.inputs["Image"])
        links.new(glare_node.outputs["Image"], composite_node.inputs["Image"])

    def set_freestyle(self, line_thickness=.5):
        freestyle = self.scene.view_layers[0].freestyle_settings
        lineset = freestyle.linesets[0]
        
        LineSetV = freestyle.linesets.new('VisibleLineset')
        LineSetV.select_by_visibility = True
        LineSetV.select_by_edge_types = True
        LineSetV.select_by_face_marks = False
        LineSetV.select_by_image_border = False
        lineset.linestyle = LineSetV.linestyle

        self.scene.render.use_freestyle = True
        self.scene.render.line_thickness = line_thickness
