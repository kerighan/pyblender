import mathutils
import numpy as np


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
    rot_quat = mathutils.Vector(direction).to_track_quat('-Z', 'Y')
    print(direction)
    print(rot_quat.to_euler())
    obj.rotation_euler = rot_quat.to_euler()
