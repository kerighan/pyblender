import numpy as np
from experiments.black_hole.materials import (create_black_hole_mat,
                                              create_sky_mat)
from pyblender import Camera, Scene
from pyblender.light import PointLight, Sun
from pyblender.material import EmissionMaterial, Material, RefractionBSDF
from pyblender.mesh import Box, IcoSphere, Plane, UVSphere
from pyblender.texture import Image


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
light = PointLight((0, -3, 0), color="#532FD1", energy=500)
light = PointLight((0, 3, 0), color="#F94159", energy=500)

# create sky
sky = UVSphere(radius=200, location=(0, 0, 100), material=create_sky_mat())
sky.shade_smooth()

# create black hole
black_hole = UVSphere(material=create_black_hole_mat(),
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

camera = Camera((40, 0, 1.5), rotation=(45, 0, 0), lens=150)
# camera.rotate(1, 0, 0)
# camera.look_at((0, 0, 0))
# camera.obj.delta_rotation_euler = (-np.pi / 12, 0.01, -0.03)
scene = Scene(camera)
# scene.set_animation_bounds(0, 199)
scene.render("render.png",
             use_ssr_refraction=True,
             eevee=True,
             size=(1920, 1080),
             samples=64,
             frame_rate=24)
