"""A grid displaced by a height map, with a glowing slab hovering above it."""

import pyblender as pb

heightmap = pb.Image("assets/heightmap.jpeg")

ground = pb.Grid(width=700, height=700, material=pb.Material(color="#DDDDDD", roughness=0.9))
pb.Displacement(ground, heightmap, strength=0.3)

slab_location = (-0.1, 0, 0.03)
slab = pb.Cube(location=slab_location, scale=(0.15, 0.3, 0.01),
               material=pb.Material(emission_strength=2))
slab.look_at((0.8, 0, 0.2))
pb.SpotLight(slab_location, energy=60)
pb.SpotLight((-0.5, -0.5, 1), energy=60)

camera = pb.Camera((0.8, 0, 0.2)).look_at((0, 0, 0.1))
scene = pb.Scene(camera)
scene.render("renders/heightmap.png", fast=False, size=(960, 540))
