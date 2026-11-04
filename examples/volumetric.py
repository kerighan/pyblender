"""A sphere lit by a colored spot inside a fog volume (god rays)."""

import pyblender as pb

fog = pb.Cube(size=10, rotation=(0, 0, 0.7), material=pb.VolumeMaterial(density=0.1))
sphere = pb.Sphere(radius=0.3, div=128, material=pb.Material())
light = pb.SpotLight((2, 2, 2), focus_point=(0, 0, 0), energy=2000, color="#6ACEFB",
                     blend=0.15, angle=17)

camera = pb.Camera((4, 0, 0)).look_at((0, 0, 0))
scene = pb.Scene(camera)
scene.render("renders/volumetric.png", fast=False, size=(1920, 1080))
