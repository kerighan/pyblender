"""Time units: the high-level API (tweens, motions, bursts, ``render(duration=)``) takes
seconds, converted to frames with ``pb.defaults.fps``. Changing the frame rate then
keeps every animation the same length, only smoother.

The low-level ``animate_*`` methods and ``Timeline`` work with raw frames.

::

    cube.to(scale=2, duration=0.5)        # half a second, 15 frames at 30 fps
    cube.to(scale=1, duration=pb.frames(15))   # exactly 15 frames whatever the fps
"""


class Defaults:
    """Package-wide defaults, editable: ``pb.defaults.fps = 60``."""

    size = (1280, 720)
    engine = "eevee"      # "eevee" or "cycles"
    samples = None        # None keeps Blender's defaults
    fps = 30
    crf = 18
    gpu = True

    @property
    def frame_rate(self):
        return self.fps

    @frame_rate.setter
    def frame_rate(self, value):
        self.fps = value


defaults = Defaults()


class Frames(int):
    """An explicit number of frames, passed through untouched by :func:`to_frames`."""


def frames(count):
    """Mark a duration as an exact number of frames: ``duration=pb.frames(15)``."""
    return Frames(round(count))


def to_frames(seconds):
    """Convert seconds (or :class:`Frames`) to an integer frame count."""
    if isinstance(seconds, Frames):
        return int(seconds)
    return int(round(float(seconds) * defaults.fps))


def to_seconds(frame_count):
    return frame_count / defaults.fps
