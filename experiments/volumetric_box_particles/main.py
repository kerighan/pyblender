import numpy as np
from pyblender import Camera, Scene
from pyblender.force import Turbulence
from pyblender.light import PointLight
from pyblender.material import Material, VolumeMaterial
from pyblender.mesh import Box, Cube, IcoSphere, Particles

cube_mat = Material()

tgt = Box(material=cube_mat,
          location=(1000, 1000, 1000), size=.5)
src = IcoSphere((0, 0, 0), radius=.05)
particles = Particles(src, tgt, gravity=0, count=500,
                      frames=(-1, 1),
                      size_random=.3,
                      factor_random=5,
                      lifetime_random=0,
                      lifetime=800,
                      phase_factor_random=1,
                      time_tweak=.15,
                      rotation_factor_random=1,
                      angular_velocity_factor=1)

volume_mat = VolumeMaterial(color="#FFFFFF", density=.5)
volume = Cube((0, 0, 0), size=10, material=volume_mat)

Turbulence(strength=50, flow=10)

point = PointLight((0, 0, 0), energy=20)
point.animate_energy([22, 12, 0], [0, 5*60, 6*60])

camera = Camera(location=(5, 0, 0))
camera.look_at((0, 0, 0))
# camera.animate_location([(6, 0, 0), (2, 0, 0)], [0, 6*60])

scene = Scene(camera)
scene.set_animation_bounds(0, 60*6)
# scene.add_bloom(radius=2, intensity=.05, threshold=.9)
scene.render("render.mp4", size=(900, 900), fast=True)
