"""Several scenes in one script, joined into one video with crossfades.

::

    movie = pb.Movie("trailer.mp4", fade=0.5, size=(1280, 720))

    @movie.shot(duration=4)
    def opening():
        pb.Text("hello", split="letters").parts.pop_in()
        pb.Camera((0, -8, 0), target=(0, 0, 0))

    @movie.shot(duration=5, transition="cut")
    def cubes():
        pb.Group(pb.Cube(location=(i, 0, 0)) for i in range(5)).from_(scale=0, stagger=0.1)

    movie.render()          # resets Blender between shots, renders each one, joins them

A shot function builds a scene from scratch (Blender is reset before it runs) and may
tune ``pb.scene()`` or ``pb.post``; the camera and light are automatic when missing.
It can return a :class:`~pyblender.scene.Scene` to render with instead of the default one.
"""

import json
import os
import shutil
import subprocess

from . import quick
from .timing import defaults


class Shot:
    def __init__(self, build, duration, name, transition, render_kwargs):
        self.build = build
        self.duration = duration
        self.name = name
        self.transition = transition
        self.render_kwargs = render_kwargs
        self.path = None


class Movie:
    """A sequence of shots rendered one after the other and joined into ``filename``.

    Arguments:
        filename: the final ``.mp4``.
        fade: default crossfade length in seconds between shots (0 for hard cuts).
        size, samples, engine: render settings shared by the shots.
        workdir: where the individual shot videos go (next to ``filename`` by default).
    """

    def __init__(self, filename, fade=0.5, size=None, samples=None, engine=None, workdir=None):
        self.filename = os.path.abspath(filename)
        self.fade = fade
        self.render_kwargs = {"size": size, "samples": samples, "engine": engine}
        self.workdir = workdir or os.path.splitext(self.filename)[0] + "_shots"
        self.shots = []

    def shot(self, duration, name=None, transition="fade", **render_kwargs):
        """Decorator registering a shot: ``@movie.shot(duration=4)``.

        ``transition`` is how the shot joins the previous one: ``"fade"`` (crossfade of
        ``movie.fade`` seconds, or a number of seconds) or ``"cut"``.
        """
        def register(build):
            self.add(build, duration, name or build.__name__, transition, **render_kwargs)
            return build
        return register

    def add(self, build, duration, name=None, transition="fade", **render_kwargs):
        """Register a shot from a function (same as the decorator)."""
        self.shots.append(Shot(build, duration, name or build.__name__, transition, render_kwargs))
        return self

    def add_file(self, path, transition="fade"):
        """Insert an existing video (a shot rendered earlier, a logo animation…)."""
        shot = Shot(None, None, os.path.basename(path), transition, {})
        shot.path = os.path.abspath(path)
        self.shots.append(shot)
        return self

    # ------------------------------------------------------------------

    def render_shot(self, shot, index):
        """Render one shot into the work directory and return its path."""
        import pyblender as pb

        if shot.build is None:
            return shot.path
        pb.reset()
        scene = shot.build()
        if scene is None:
            scene = quick.scene()
        if scene.scene.camera is None:
            quick.auto_camera()
        if not any(obj.type == "LIGHT" for obj in scene.scene.objects):
            quick.auto_light()
        kwargs = {k: v for k, v in self.render_kwargs.items() if v is not None}
        kwargs.update(shot.render_kwargs)
        path = os.path.join(self.workdir, f"{index:02d}_{shot.name}.mp4")
        shot.path = scene.render(path, duration=shot.duration, **kwargs)
        return shot.path

    def render(self, only=None, force=True):
        """Render the shots (all, or those named in ``only``) and join them.

        With ``force=False`` a shot whose video already exists is not rendered again,
        handy while iterating on one shot.
        """
        os.makedirs(self.workdir, exist_ok=True)
        for index, shot in enumerate(self.shots):
            expected = os.path.join(self.workdir, f"{index:02d}_{shot.name}.mp4")
            if shot.build is None:
                continue
            if only is not None and shot.name not in only:
                shot.path = expected if os.path.exists(expected) else shot.path
                continue
            if not force and os.path.exists(expected):
                shot.path = expected
                continue
            self.render_shot(shot, index)
        missing = [s.name for s in self.shots if s.path is None or not os.path.exists(s.path)]
        if missing:
            raise RuntimeError(f"shots without a video: {missing}")
        fades = []
        for shot in self.shots[1:]:
            if shot.transition == "fade":
                fades.append(self.fade)
            elif shot.transition == "cut":
                fades.append(0)
            else:
                fades.append(float(shot.transition))
        join([s.path for s in self.shots], fades, self.filename)
        return self.filename


def video_duration(path):
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                            "json", path], capture_output=True, text=True, check=True)
    return float(json.loads(probe.stdout)["format"]["duration"])


def join(paths, fades, filename, crf=None):
    """Concatenate videos with ffmpeg; ``fades[i]`` is the crossfade (seconds, 0 = cut)
    between ``paths[i]`` and ``paths[i + 1]``."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is needed to join videos")
    durations = [video_duration(p) for p in paths]
    inputs = [arg for p in paths for arg in ("-i", p)]
    filters, offset, previous = [], 0.0, "[0:v]"
    for index in range(1, len(paths)):
        fade = fades[index - 1]
        offset += durations[index - 1] - fade
        label = f"[v{index}]"
        if fade > 0:
            filters.append(f"{previous}[{index}:v]xfade=transition=fade:duration={fade}:"
                           f"offset={offset:.3f}{label}")
        else:
            filters.append(f"{previous}[{index}:v]concat=n=2:v=1:a=0{label}")
        previous = label
    cmd = ["ffmpeg", "-loglevel", "error", "-y", *inputs]
    if filters:
        cmd += ["-filter_complex", ";".join(filters), "-map", previous]
    cmd += ["-c:v", "libx264", "-crf", str(defaults.crf if crf is None else crf),
            "-pix_fmt", "yuv420p", "-r", str(defaults.fps), filename]
    subprocess.run(cmd, check=True)
    return filename
