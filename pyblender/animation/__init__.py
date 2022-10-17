from .utils import assert_list_is_sorted
from ..utils import hex_to_rgb
from .easing import tween
import numpy as np
import addict
import copy


def linear(values, frames):
    val = np.linspace(values[0], values[1], frames[1] - frames[0])
    frames = list(range(frames[0], frames[1] + 1))
    return val, frames


def shake(frames, origin, freq, intensity):
    n_frames = frames[1] - frames[0]
    n_k = int(round(freq*n_frames))
    # keyframes = np.random.randint(
    #     frames[0], frames[1], size=n_k - 1)
    keyframes = np.linspace(frames[0], frames[1], n_k-1).astype(int)
    values = np.random.normal(size=(n_k, 3), scale=intensity)
    origin = np.array(origin)
    
    keyframes = [0] + sorted(keyframes)
    tl = Timeline(*keyframes)
    tl.pos = [
        ("cubic-in-out", values[i], values[i+1])
        for i in range(len(values) - 1)
    ]
    
    val = []
    # print(tl[0])
    for frame in range(frames[0], frames[1]):
        val.append(tl[frame].pos + origin)
    return val, range(frames[0], frames[1])


class Timeline(object):
    """The timeline object is the central tool to automate parameters.
    It is passed keyframes (in milliseconds) as arguments.
    Once created, a timeline object can de added to any Element instance.
    Multiple elements can be aded to the same element.

    You can create a :class:`Timeline` instance in your main module
    or int he :file:`__init__.py` file of your package like this::

        from motion.animation import Timeline
        timeline = Timeline(0, 1000, 2000)
        timeline.x = [
            ("cubic-in-out", 0, 100),  # cubic animation between 0 and 1000ms
            ("linear", 100, 50)  # linear animation between 1000 and 2000ms
        ]
    This will animate the parameter named `x` between 0

    Arguments:
            args {floats} -- the keyframes in milliseconds

    Keyword Arguments:
        delay {float} -- delays the animation by a given offset in milliseconds
    """
    def __init__(self, *args, delay=0):
        self.init_keyframes(args)
        self._delay = delay
        self.before = addict.Dict()
        self.after = addict.Dict()
        self.dtype = addict.Dict()

    def delay(self, delay):
        timeline = copy.deepcopy(self)
        timeline._delay += delay
        timeline.start += delay
        timeline.end += delay
        return timeline

    def grad(self, name, t=0, delta=1):
        if isinstance(name, str):
            delta_value = self[t + delta][name] - self[t][name]
        elif isinstance(name, list):
            delta_value = 0
            after = self[t + delta]
            current = self[t]
            for item in name:
                delta_value += after.get(item, 0) - current.get(item, 0)
        return delta_value / delta

    def x_grad(self, t=0, delta=1):
        return self.grad(["offset_x", "x"])

    def y_grad(self, t=0, delta=1):
        return self.grad(["offset_y", "y"])

    def init_keyframes(self, args):
        # make sure keyframes are in order
        assert_list_is_sorted(args)

        # init keyframes and animation bounds
        self.keyframes = args
        self.end = self.keyframes[-1]
        self.start = self.keyframes[0]

        # create animation segments
        segments = []
        for start, end in zip(args, args[1:]):
            segments.append({
                "start": start,
                "end": end,
                "attributes": {}
            })
        self.segments = segments

    def __setattr__(self, name, value):
        if name in {
            "keyframes", "_delay", "segments",
            "before", "after", "start", "end", "dtype"
        }:
            super().__setattr__(name, value)
        else:
            # make sure the number of segments is the same as the input
            assert len(value) == len(self.segments)

            for i, segment in enumerate(self.segments):
                # in case input is color hex
                v = value[i]
                v_1 = v[1]
                if isinstance(v[1], str) and v[1][0] == "#":
                    v_1 = np.array(hex_to_rgb(v[1]))
                if len(v) == 3:
                    v_2 = v[2]
                    if isinstance(v[2], str) and v[2][0] == "#":
                        v_2 = np.array(hex_to_rgb(v[2]))
                    segment["attributes"][name] = (v[0], v_1, v_2)
                else:
                    segment["attributes"][name] = (v[0], v_1)

    def get_attributes(self, segment, t_unit):
        """Build attributes Dict for a given segment and time.

        Arguments:
            segment {dict} -- segment between two keyframes
            t_unit {float} -- unitless time between 0 and 1

        Returns:
            attributes {addict.Dict} -- computed attributes
        """
        attributes = addict.Dict()
        for attribute in segment["attributes"]:
            # easing is the easing name
            result = segment["attributes"][attribute]
            if len(result) == 3:
                easing, a, b = result
            else:
                easing, a = result
                b = None
            value = tween(easing, a, b, t_unit)
            if attribute in self.dtype:
                value = self.dtype[attribute](value)
            attributes[attribute] = value
        return attributes

    def __getitem__(self, t_):
        """Evaluates all animated attributes at time t.

        Arguments:
            t {float} -- input time in milliseconds

        Returns:
            attributes {addict.Dict} -- attributes computed at timestep t
        """
        t = t_ - self._delay
        if t < self.segments[0]["start"]:
            if len(self.before) > 0:
                attr = self.before
                attr.t = t_
                return attr
            attr = self.get_attributes(self.segments[0], 0)
            attr.t = t_
            return attr
        elif t > self.segments[-1]["end"]:
            if len(self.after) > 0:
                attr = self.after
                attr.t = t_
                return attr
            attr = self.get_attributes(self.segments[-1], 1)
            attr.t = t_
            return attr
        for segment in self.segments:
            start = segment["start"]
            end = segment["end"]
            if start <= t <= end:
                # normalize time so that easing can be computed
                t_unit = (t - start) / (end - start)
                attr = self.get_attributes(segment, t_unit)
                attr.t = t_
                return attr


class Cycle(Timeline):
    def __getitem__(self, t_):
        """Evaluates all animated attributes at time t.

        Arguments:
            t {float} -- input time in milliseconds

        Returns:
            attributes {addict.Dict} -- attributes computed at timestep t
        """
        t = t_ - self._delay
        t = t % self.end
        if t < self.segments[0]["start"]:
            if len(self.before) > 0:
                attr = self.before
                attr.t = t_
                return attr
            attr = self.get_attributes(self.segments[0], 0)
            attr.t = t_
            return attr
        elif t > self.segments[-1]["end"]:
            if len(self.after) > 0:
                attr = self.after
                attr.t = t_
                return attr
            attr = self.get_attributes(self.segments[-1], 1)
            attr.t = t_
            return attr
        for segment in self.segments:
            start = segment["start"]
            end = segment["end"]
            if start <= t <= end:
                # normalize time so that easing can be computed
                t_unit = (t - start) / (end - start)
                attr = self.get_attributes(segment, t_unit)
                attr.t = t_
                return attr


def in_out(attack=400, hold=2000, release=400):
    tl = Timeline(0, attack, attack + hold, attack + hold + release)
    return tl


def slide_up(
    item,
    attack=600,
    duration=3000,
    release=600,
    delay=0,
    amount=2,
    easing="cubic-in-out"
):
    anim = in_out(attack, duration, release)
    anim.offset_y = [
        (easing, amount, 0),
        ("constant", 0),
        (easing, 0, -amount)
    ]
    anim.opacity = [(easing, 0, 1), ("constant", 1), (easing, 1, 0)]
    item += anim.delay(delay)


def highlight(
    item, scene,
    attack=600,
    duration=2000,
    release=600,
    delay=0,
    color="#b94188",
    easing="cubic-in-out",
    margin_width=1, margin_height=1
):
    from motion.shape import Rectangle
    item.size = scene.size
    z_index = item.z_index - 1
    bboxes = item.line_bbox()

    for bbox in bboxes:
        width = bbox["width"] + 2 * margin_width
        height = bbox["height"] + 2 * margin_height
        encart = Rectangle(
            width=width, height=height,
            color=color, align="top-left",
            z_index=z_index)
        encart.x = bbox["x"][0] - margin_width
        encart.y = bbox["y"][0] - margin_height
        tl_encart = in_out(attack, duration, release)
        tl_encart.width = [
            (easing, 0, width),
            ("constant", width),
            (easing, width, 0)]
        encart += tl_encart.delay(delay)
    return encart


class Movement:
    def __init__(self, velocity=.05, use_rotation=False):
        self.use_rotation = use_rotation
        self.velocity = velocity
        self.frames = []
        self.rotation_frames = []
    
    def start_at(self, x, y, z):
        pos = np.array([x, y, z])
        self.last_order = pos
        self.last_pos = pos
        self.frames.append(pos)
        self.rotation_frames.append((0, 0, 0))
    
    def move_to(self, x, y, z):
        pos = np.array([x, y, z])
        last_pos = self.frames[-1]
        distance = np.sum((pos - last_pos)**2)**.5
        n_frames = round(distance/self.velocity)
        
        direction = pos - self.last_order
        self.last_order = pos
        if direction[0] == 0:
            z_angle = 90 if direction[1] > 0 else -90
        else:
            z_angle = np.arcsin(direction[1] / direction[0])
        
        for i in range(1, n_frames+1):
            t = i / n_frames
            interp = t * pos + (1-t)*last_pos
            self.frames.append(interp)
            self.rotation_frames.append((90, 0, z_angle))
    
    def apply(self, mesh):
        mesh.animate_location(self.frames)
        if self.use_rotation:
            mesh.animate_rotation(self.rotation_frames)

    @property
    def duration(self):
        return len(self.frames)
    

def flicker(n_steps, step_size, start_with=True):
    unit = [start_with] * step_size + [not start_with] * step_size
    return unit * n_steps
