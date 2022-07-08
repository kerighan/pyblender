from pyblender import Scene
from pyblender.camera import Camera
from pyblender.light import Sun
from pyblender.material import Material
from pyblender.mesh import Box

mat = Material()

# create nodes
bsdf = mat.bsdf
color_ramp = mat.create_color_ramp(colors=["#FF0000", "#00FF00"])
noise_texture = mat.create_noise_texture()
multiply = mat.create_multiply(value=.1)
mat.link(noise_texture, multiply, "Fac", 0)

mat.link(noise_texture, bsdf, "Fac", "Base Color")
mat.link(multiply, mat.material_output, "Value", "Displacement")

# mat = Material()

Box(location=(0, -1, 0), material=mat)
Box(location=(0, 1, 0), material=mat)

Sun()

camera = Camera((10, 0, 0))
camera.look_at((0, 0, 0))

scene = Scene(camera)
scene.add_bloom()
scene.render("render.png", fast=True)