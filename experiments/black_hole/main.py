from experiments.black_hole.materials import create_sky_mat, create_black_hole_mat
from pyblender import Scene, Camera
from pyblender.mesh import IcoSphere, Plane, Box, UVSphere
from pyblender.material import Material, EmissionMaterial, RefractionBSDF
from pyblender.light import Sun
from pyblender.texture import Image
import numpy as np


def get_rotation(R, N, i):
    rot = []
    for k in range(200):
        phase = 2*np.pi * k / 15
        x = 2 * np.pi * i / N + phase
        y = 2 * np.pi * i / N + phase
        if i % 2 == 0:
            rot.append((0, y, x))
        else:
            rot.append((y, -x, 0))
    return rot


def get_position(R, N, i):
    rot = []
    for k in range(200):
        phase = 2*np.pi * k / 100
        x = R * np.cos(2 * np.pi * i / N + phase)
        y = R * np.sin(2 * np.pi * i / N + phase)
        rot.append((x, y, 0))
    return rot


rand = np.random.random
Sun(energy=1, location=(0, 0, 5))

# create sky
sky = UVSphere(radius=200, location=(0, 0, 100), material=create_sky_mat())
sky.shade_smooth()

# create black hole
black_hole = IcoSphere(material=create_black_hole_mat(),
                       radius=2, div=8)
black_hole.shade_smooth()


N = 50
R = 3.3
box_mat = Material(color="#FFFFFF")
for i in range(N):
    x = R * np.cos(2 * np.pi * i / N)
    y = R * np.sin(2 * np.pi * i / N)
    box = Box(location=(x, y, 0), size=rand() / 2,
              rotation=(rand(), rand(), rand()),
              material=box_mat)
    
    box.animate_location(get_position(R, N, i))
    box.animate_rotation(get_rotation(R, N, i))

camera = Camera((12, 0, 1.5))
camera.look_at((0, 0, 0))
camera.obj.delta_rotation_euler = (-np.pi / 12, 0.01, -0.03)
scene = Scene(camera)
scene.set_animation_bounds(0, 199)
scene.render("render.mp4",
             use_ssr_refraction=True,
             eevee=True,
             size=(1000, 1000),
             samples=64,
             frame_rate=24)
