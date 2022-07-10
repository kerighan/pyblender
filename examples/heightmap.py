import pyblender as pb
from pyblender.texture import Image
from pyblender.modifier import Displacement

pb.SpotLight((-.5, -.5, 1), energy=60)
image = Image("index.jpeg")
texture = Image("texture.jpg")

# add plane
plane_mat = pb.Material(color="#DDDDDD", roughness=.9)
plane = pb.Grid(width=700, height=700, material=plane_mat)
displacement = Displacement(plane, image, strength=.3)

loc = (-.1, 0, .03)
cube_mat = pb.Material(color="#FFFFFF", emissive=2)
cube = pb.Box(scale=(.15, .3, .01), size=1,
              location=loc, material=cube_mat)
pb.SpotLight(loc, energy=60)
cube.look_at((.8, 0, .2))

camera = pb.Camera((.8, 0, .2))
camera.look_at((0, 0, 0.1))

scene = pb.Scene(camera)
scene.scene.gravity = 0
# scene.add_bloom(intensity=.2, threshold=.9, radius=5)
scene.render("heightmap.png", fast=False, size=(1920//2, 1080//2))
