import numpy as np
from pyblender import Scene
from pyblender.camera import Camera
from pyblender.light import PointLight, SpotLight, Sun
from pyblender.material import Material, RefractionBSDF
from pyblender.mesh import Box, Grid, Plane
from pyblender.texture import Noise, Texture

# Sun()

plane_mat = Material(displace=True)
disp = plane_mat.create_displacement(scale=3, midlevel=0)
noise = plane_mat.create_noise_texture(scale=3, detail=16)
noise_2 = plane_mat.create_noise_texture(scale=400, detail=16)
cr = plane_mat.create_color_ramp(positions=[.37, 1],
                                 interpolation="EASE")
noise["Fac"].to(cr["Fac"])
cr["Color"].to(disp["Height"])
disp[0].to(plane_mat.material_output["Displacement"])

noise_2["Fac"].to(plane_mat.bsdf["Roughness"])
noise_2["Fac"].to(plane_mat.bsdf["Metallic"])

plane = Grid(
    size=10,
    rotation=(0, 0, np.pi / 5),
    location=(.5, -.5, 0),
    material=plane_mat,
    width=100,
    height=100)
plane.modify_subdivide()


monolith_mat = RefractionBSDF(ior=1.1, roughness=.9)
# noise_3 = monolith_mat.create_noise_texture(
#     scale=200, detail=8, distortion=.5)
# noise_3["Fac"].to(monolith_mat.bsdf["Roughness"])
monolith = Box(scale=(.3, 1.2, 2.7), size=.1,
               rotation=(0, 0, 3.141/6),
               location=(3.5, 0, 0.11),
               material=monolith_mat)

PointLight((.5, 0, .5))


camera = Camera(location=(4, 0, .1), lens=30)
camera.look_at((0, 0, .1))
scene = Scene(camera)
scene.render("render.png", eevee=False, size=(1920, 1080), samples=4096)
