import numpy as np
from experiments.monolith.materials import create_sky_mat, create_terrain_mat
from pyblender import Scene
from pyblender.camera import Camera
from pyblender.light import PointLight, SpotLight, Sun
from pyblender.material import Material, RefractionBSDF, VolumeMaterial
from pyblender.mesh import Box, Grid, Plane, UVSphere
from pyblender.texture import Image, Noise, Texture

FRAME_RATE = 60


# TERRAIN
# =======
plane = Grid(
    size=10,
    rotation=(0, 0, np.pi / 5),
    location=(.5, -.5, 0),
    material=create_terrain_mat(),
    width=100, height=100)
plane.modify_subdivide(render_levels=2)

# SKY
# ===
sky = UVSphere(radius=200, location=(0, 0, 100), material=create_sky_mat())
sky.shade_smooth()
sky.animate_rotation([(0, 0, 0), (0, 0, .1)], [0, FRAME_RATE*5])

# MONOLITH
# ========
monolith_mat = Material(
    roughness=.5, color="#2C2B2B")
monolith = Box(scale=(.2, 1.2, 2.7), size=.1,
               rotation=(0, 0, 3.141/6),
               location=(3.48, 0, 0.12),
               material=monolith_mat)
wf_mat = Material(emission_strength=5, color="#FFFFFF")
wf = Box(scale=(.2, 1.2, 2.7), size=.1,
         rotation=(0, 0, 3.141/6),
         location=(3.48, 0, 0.12),
         material=wf_mat)
wf.modify_wireframe(thickness=.0008)

# LIGHTING
# ========
PointLight((1.9, 0, .05), energy=20)
PointLight((1.5, 2.3, .5), energy=100, color="#FF1F02")
PointLight((-1.5, 2.3, .5), energy=50, color="#009CF8")
PointLight((1.6, -2.3, .5), energy=30, color="#009CF8")
spot = SpotLight((3., 0, 0.12), energy=20)
spot.look_at((4, 0, .1))

# SCENE, CAMERA AND RENDER
# ========================
camera = Camera(location=(4, 0, .1), lens=30)
camera.look_at((0, 0, .1))
camera.animate_location([(6, 0, 0.2), (4, 0, .1)], [0, FRAME_RATE*5])
scene = Scene(camera)
scene.set_animation_bounds(0, FRAME_RATE*5)
scene.add_glare()
scene.render("render.mp4", eevee=False,
             size=(1920, 1080),
             samples=4096, frame_rate=FRAME_RATE)
