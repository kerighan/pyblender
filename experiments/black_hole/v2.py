from math import radians

import numpy as np
from experiments.materials import (create_black_hole_mat, create_sky_mat,
                                   create_smoke_mat)
from pyblender import Camera, Scene, material
from pyblender.light import PointLight, Sun
from pyblender.material import EmissionMaterial, Material, VolumeMaterial
from pyblender.mesh import Circle, Cylinder, Empty, IcoSphere, Line, UVSphere
from pyblender.texture import Noise

# create sky
sky = UVSphere(radius=200, location=(0, 0, 100), material=create_sky_mat())
sky.shade_smooth()

# create black hole
# black_hole = UVSphere(material=create_black_hole_mat(), radius=2, div=48)
# black_hole.shade_smooth()

camera = Camera((50, 0, 0), lens=150)
camera.look_at((0, 0, 0))
scene = Scene(camera)
# scene.add_glare(saturation=1.25)
# scene.set_animation_bounds(1, 120)
scene.render("render.png",
             use_ssr_refraction=True,
             eevee=True,
             size=(1920//2, 1080//2),
             samples=16, frame=1,
             frame_rate=60)
