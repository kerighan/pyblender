import glob
import os
import shutil
import subprocess
import warnings

import bpy


class Scene:
    """Render settings and output for the current Blender scene.

    Arguments:
        camera: the :class:`~pyblender.camera.Camera` used for rendering.
    """

    def __init__(self, camera):
        self.camera = camera
        self.scene = bpy.context.scene
        self.scene.camera = camera.obj
        self.animation = False
        self._post = None

    @property
    def post(self):
        """Post-processing stack, see :class:`~pyblender.post.PostProcess`."""
        if self._post is None:
            from .post import PostProcess
            self._post = PostProcess(self.scene)
        return self._post

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def set_animation_bounds(self, start=0, end=100):
        """Make :meth:`render` produce an animation spanning frames ``start``..``end``."""
        self.scene.frame_start = start
        self.scene.frame_end = end
        self.animation = True
        return self

    def set_gravity(self, gravity=(0, 0, -9.81)):
        self.scene.gravity = gravity
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

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, filename, size=(1280, 720), fast=True, gpu=True, samples=None,
               frame_rate=30, crf=18):
        """Render to ``filename``.

        * ``.png`` renders a still image, or the animation as ``0001.png``…
          in that folder when ``filename`` ends with ``/``.
        * ``.mp4`` renders every frame to a temporary folder next to the file
          and encodes them with ffmpeg.

        Arguments:
            fast: use Eevee (fast) rather than Cycles (path tracing, slow but accurate).
            gpu: use the GPU for Cycles.
            samples: number of render samples, ``None`` keeps Blender defaults.
            frame_rate, crf: video frame rate and quality (lower crf = better).
        """
        render = self.scene.render
        render.engine = "BLENDER_EEVEE" if fast else "CYCLES"
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
            animation = self.animation

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
