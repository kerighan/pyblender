import glob
import os
import shutil
import subprocess
import warnings

import bpy

from .utils import to_rgba


class Defaults:
    """Package-wide render defaults, editable: ``pb.defaults.engine = "cycles"``."""

    size = (1280, 720)
    engine = "eevee"      # "eevee" or "cycles"
    samples = None        # None keeps Blender's defaults
    frame_rate = 30
    crf = 18
    gpu = True


defaults = Defaults()

ENGINES = {"eevee": "BLENDER_EEVEE", "cycles": "CYCLES"}


def _engine(engine=None, fast=None, cycles=None):
    """Resolve the three ways of choosing a render engine into ``"eevee"`` / ``"cycles"``."""
    if cycles is not None:
        return "cycles" if cycles else "eevee"
    if fast is not None:
        return "eevee" if fast else "cycles"
    if engine is None:
        return defaults.engine
    engine = engine.lower()
    if engine not in ENGINES:
        raise ValueError(f"engine must be 'eevee' or 'cycles', got {engine!r}")
    return engine


class Scene:
    """Render settings and output for the current Blender scene.

    Arguments:
        camera: the :class:`~pyblender.camera.Camera` used for rendering. Defaults to the
            last camera created.
        size: output resolution, can also be given to :meth:`render`.
        engine: ``"eevee"`` (fast) or ``"cycles"`` (path tracing). ``fast=False`` and
            ``cycles=True`` are accepted too.
        samples: render samples, ``None`` keeps Blender's defaults.
        frames: number of frames of the animation (``frames=120`` renders 0..119).
    """

    def __init__(self, camera=None, size=None, engine=None, samples=None, frames=None,
                 fast=None, cycles=None):
        self.scene = bpy.context.scene
        if camera is not None:
            self.scene.camera = camera.obj
        self.camera = camera
        self.size = defaults.size if size is None else size
        self.engine = _engine(engine, fast, cycles)
        self.samples = defaults.samples if samples is None else samples
        self.animation = False
        self._post = None
        if frames is not None:
            self.frames = frames

    @property
    def fast(self):
        return self.engine == "eevee"

    @fast.setter
    def fast(self, value):
        self.engine = "eevee" if value else "cycles"

    @property
    def frames(self):
        """Number of frames of the animation; setting it renders frames ``0..frames-1``."""
        return self.scene.frame_end - self.scene.frame_start + 1

    @frames.setter
    def frames(self, count):
        self.set_animation_bounds(0, int(count) - 1)

    def set(self, **properties):
        """Set any property of the Blender scene, its render, Eevee or Cycles settings:
        ``scene.set(frame_step=2, film_transparent=True, taa_render_samples=16)``."""
        for name, value in properties.items():
            for holder in (self.scene, self.scene.render, self.scene.eevee, self.scene.cycles,
                           self.scene.view_settings):
                if hasattr(holder, name):
                    setattr(holder, name, value)
                    break
            else:
                raise AttributeError(f"scene has no property {name!r}")
        return self

    @property
    def post(self):
        """Post-processing stack, see :class:`~pyblender.post.PostProcess`."""
        if self._post is None:
            from .post import PostProcess
            self._post = PostProcess(self.scene)
        return self._post

    compositor = post

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def set_animation_bounds(self, start=0, end=100):
        """Make :meth:`render` produce an animation spanning frames ``start``..``end``."""
        self.scene.frame_start = start
        self.scene.frame_end = end
        self.animation = True
        return self

    def set_frame(self, frame):
        self.scene.frame_set(frame)
        return self

    def set_gravity(self, gravity=(0, 0, -9.81)):
        self.scene.use_gravity = True
        self.scene.gravity = gravity
        return self

    def set_background(self, color="#000000", strength=1.0, image=None):
        """World background: a color, or an image (HDRI or plain) that also lights the scene."""
        world = self.scene.world or bpy.data.worlds.new("world")
        self.scene.world = world
        world.use_nodes = True
        nodes = world.node_tree.nodes
        background = nodes["Background"]
        background.inputs["Strength"].default_value = strength
        if image is None:
            background.inputs["Color"].default_value = to_rgba(color)
        else:
            from .texture import Image
            environment = nodes.new("ShaderNodeTexEnvironment")
            environment.image = (image if isinstance(image, Image) else Image(image)).img
            world.node_tree.links.new(environment.outputs["Color"], background.inputs["Color"])
        return self

    def set_color_management(self, view_transform="Filmic", look="None", exposure=0.0,
                             gamma=1.0):
        """``view_transform`` is ``"Filmic"`` or ``"Standard"``; ``look`` a contrast preset such
        as ``"Medium High Contrast"``."""
        view = self.scene.view_settings
        view.view_transform = view_transform
        view.look = look
        view.exposure = exposure
        view.gamma = gamma
        return self

    def set_eevee(self, ssr=True, refraction=False, gtao=True, motion_blur=False,
                  soft_shadows=True, volumetric_tile_size="8", volumetric_samples=64):
        """Eevee quality switches: screen-space reflections / refraction, ambient
        occlusion, motion blur, volumetric resolution."""
        eevee = self.scene.eevee
        eevee.use_ssr = ssr
        eevee.use_ssr_refraction = refraction
        eevee.use_gtao = gtao
        eevee.use_motion_blur = motion_blur
        eevee.use_soft_shadows = soft_shadows
        eevee.volumetric_tile_size = str(volumetric_tile_size)
        eevee.volumetric_samples = volumetric_samples
        return self

    def set_motion_blur(self, enabled=True, shutter=0.5):
        self.scene.eevee.use_motion_blur = enabled
        self.scene.render.use_motion_blur = enabled
        self.scene.render.motion_blur_shutter = shutter
        return self

    def set_transparent(self, transparent=True):
        """Render with a transparent background (PNG with alpha)."""
        self.scene.render.film_transparent = transparent
        return self

    def set_freestyle(self, line_thickness=0.5):
        """Draw outlines around objects (Freestyle)."""
        freestyle = self.scene.view_layers[0].freestyle_settings
        lineset = freestyle.linesets[0] if freestyle.linesets else freestyle.linesets.new("lines")
        if lineset.linestyle is None:
            lineset.linestyle = bpy.data.linestyles.new("lines")
        lineset.select_by_visibility = True
        lineset.select_by_edge_types = True
        self.scene.render.use_freestyle = True
        self.scene.render.line_thickness = line_thickness
        return self

    def add_bloom(self, intensity=0.05, radius=2.0, threshold=0.8):
        """Eevee bloom: makes emissive materials and bright lights glow."""
        eevee = self.scene.eevee
        eevee.use_bloom = True
        eevee.bloom_intensity = intensity
        eevee.bloom_radius = radius
        eevee.bloom_threshold = threshold
        return self

    def add_volumetric_light(self, shadows=True):
        """Eevee volumetric lighting, needed to see :class:`~pyblender.material.VolumeMaterial`."""
        self.scene.eevee.use_volumetric_lights = True
        self.scene.eevee.use_volumetric_shadows = shadows
        return self

    def add_glare(self, size=8, mix=0.0, threshold=1.0, dispersion=0.01, saturation=1.1,
                  contrast=1.0, gain=1.1):
        """A classic finishing stack: lens dispersion, color correction and fog glow."""
        post = self.post
        post.chromatic_aberration(dispersion, distort=-0.4 * dispersion)
        post.color_correction(saturation=saturation, contrast=contrast, gain=gain)
        post.glow(threshold=threshold, mix=mix, size=size)
        return self

    def use_gpu(self, device_type="CUDA"):
        """Render Cycles on the GPU. Silently falls back to the CPU when unavailable."""
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = device_type
            prefs.get_devices()
            for device in prefs.devices:
                device.use = device.type in (device_type, "CPU")
            self.scene.cycles.device = "GPU"
        except (TypeError, KeyError) as exc:
            warnings.warn(f"GPU rendering unavailable ({exc}), using CPU")
        return self

    def bake(self):
        """Bake every physics cache (rigid bodies, cloth, soft bodies, particles) over the
        animation range before rendering."""
        start, end = self.scene.frame_start, self.scene.frame_end
        caches = []
        if self.scene.rigidbody_world is not None:
            caches.append(self.scene.rigidbody_world.point_cache)
        for obj in self.scene.objects:
            caches += [m.point_cache for m in obj.modifiers if hasattr(m, "point_cache")]
            caches += [s.point_cache for s in obj.particle_systems]
        for cache in caches:
            cache.frame_start, cache.frame_end = start, end
        bpy.ops.ptcache.bake_all(bake=True)
        return self

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, filename, size=None, engine=None, gpu=None, samples=None, frame_rate=None,
               crf=None, frame=None, frames=None, bake=False, fast=None, cycles=None):
        """Render to ``filename``.

        * ``.png`` renders a still image, or the animation as ``0001.png``…
          in that folder when ``filename`` ends with ``/``.
        * ``.mp4`` renders every frame to a temporary folder next to the file
          and encodes them with ffmpeg.

        Arguments:
            size, engine, samples: override the values given to :class:`Scene`.
            gpu: use the GPU for Cycles.
            frame_rate, crf: video frame rate and quality (lower crf = better).
            frame: render this frame (stills only).
            frames: number of frames to render (animation ``0..frames-1``).
            bake: bake physics caches first.
        """
        if fast is not None or cycles is not None or engine is not None:
            self.engine = _engine(engine, fast, cycles)
        fast = self.fast
        size = self.size if size is None else size
        samples = self.samples if samples is None else samples
        gpu = defaults.gpu if gpu is None else gpu
        frame_rate = defaults.frame_rate if frame_rate is None else frame_rate
        crf = defaults.crf if crf is None else crf
        if frames is not None:
            self.frames = frames

        render = self.scene.render
        render.engine = ENGINES[self.engine]
        render.resolution_x, render.resolution_y = size
        render.resolution_percentage = 100
        render.image_settings.file_format = "PNG"
        render.fps = frame_rate
        if samples is not None:
            if fast:
                self.scene.eevee.taa_render_samples = samples
            else:
                self.scene.cycles.samples = samples
        if gpu and not fast:
            self.use_gpu()
        if frame is not None:
            self.scene.frame_set(frame)
        if bake:
            self.bake()

        is_folder = filename.endswith(("/", os.sep))
        filename = os.path.abspath(filename)
        is_video = filename.lower().endswith(".mp4")

        if is_video:
            frames_dir = os.path.splitext(filename)[0] + "_frames"
            shutil.rmtree(frames_dir, ignore_errors=True)
            os.makedirs(frames_dir)
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            render.filepath = os.path.join(frames_dir, "")
            animation = True
        elif is_folder:
            os.makedirs(filename, exist_ok=True)
            render.filepath = os.path.join(filename, "")
            animation = True
        else:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            render.filepath = filename
            animation = self.animation and frame is None

        bpy.ops.render.render(write_still=not animation, animation=animation)

        if is_video:
            self._encode_video(frames_dir, filename, frame_rate, crf)
            shutil.rmtree(frames_dir, ignore_errors=True)
        return filename

    @staticmethod
    def _encode_video(frames_dir, filename, frame_rate, crf):
        if not glob.glob(os.path.join(frames_dir, "*.png")):
            raise RuntimeError(f"No frame rendered in {frames_dir}")
        subprocess.run(
            [
                "ffmpeg", "-loglevel", "error", "-y",
                "-framerate", str(frame_rate),
                "-i", os.path.join(frames_dir, "%04d.png"),
                "-c:v", "libx264", "-crf", str(crf),
                "-pix_fmt", "yuv420p", "-profile:v", "main",
                "-force_key_frames", "expr:gte(t,n_forced*1)",
                filename,
            ],
            check=True,
        )
