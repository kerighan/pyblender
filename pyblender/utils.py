from math import radians

import numpy as np
from mathutils import Vector


def to_radians(rotation):
    return (radians(rotation[0]),
            radians(rotation[1]),
            radians(rotation[2]))


def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(
        int(value[i:i + lv // 3], 16)/255. for i in range(0, lv, lv // 3))


def hex_to_rgba(value, alpha=1):
    value = value.lstrip('#')
    lv = len(value)
    res = [
        int(value[i:i + lv // 3], 16)/255. for i in range(0, lv, lv // 3)]
    res += [alpha]
    return res


def look_at(obj, point):
    loc = obj.location
    direction = np.array(point) - loc
    rot_quat = Vector(direction).to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()


def random_string(length):
    import random
    import string
    return ''.join(
        random.choice(string.ascii_lowercase) for i in range(length))


def normal_in_dir(normal, direction, limit=0.5):
    return direction.dot(normal) > limit


def face_up(normal, limit=0.5):
    return normal_in_dir(normal, Vector((0, 0, 1)), limit)


def face_down(normal, limit=0.5):
    return normal_in_dir(normal, Vector((0, 0, -1)), limit)


def face_front(normal, limit=0.5):
    return normal_in_dir(normal, Vector((1, 0, 0)), limit)


def face_back(normal, limit=0.5):
    return normal_in_dir(normal, Vector((-1, 0, 0)), limit)


def face_right(normal, limit=0.5):
    return normal_in_dir(normal, Vector((0, 1, 0)), limit)


def face_left(normal, limit=0.5):
    return normal_in_dir(normal, Vector((0, -1, 0)), limit)
