import numpy as np
from pyblender import Scene
from pyblender.camera import Camera
from pyblender.light import PointLight
from pyblender.material import Material
from pyblender.mesh import Cube


def get_rotation(r, N_FRAMES, phase=0):
    rad = 2*3.141592653
    return [
        (r * np.cos(t*rad/N_FRAMES + phase),
         r * np.sin(t*rad/N_FRAMES + phase), 0)
        for t in range(N_FRAMES)]


N_ROWS = 25
PI = 3.141592653
N_FRAMES = 120
frames = range(N_FRAMES)

# add camera
camera = Camera((10, 10, 10), use_dof=True,
                focus_point=(2, 2, 2.5), aperture_fstop=.1)
camera.look_at((0, 0, 0))

# add light
light = PointLight(location=(2, 2, 2.5), energy=80)

# add cubes
cube_mat = Material(color="#FFFFFF")
for phase in np.linspace(0, 2*PI, 20, endpoint=False):
    for i, r in enumerate(np.linspace(.2, 8, N_ROWS)):
        f = PI * i / N_ROWS
        # radius = r**.5
        cube = Cube(material=cube_mat, size=1.5*(r/N_ROWS)**.7)
        cube.animate_location(
            get_rotation(r, N_FRAMES, phase=phase + PI * i / N_ROWS),
            range(N_FRAMES))
        cube.animate_rotation_z(
            np.linspace(0, 4*PI, N_FRAMES),
            range(N_FRAMES))
        cube.animate_scale_z(
            [3*(2 - np.cos(-t + 3*f)) for t in np.linspace(0, 4*PI, N_FRAMES)])

scene = Scene(camera)
scene.add_bloom(radius=10, intensity=.5, threshold=.6)
scene.set_animation_bounds(0, N_FRAMES)
scene.render("malestrom/", fast=False, size=(1000, 1000))
