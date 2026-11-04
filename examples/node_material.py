"""Build a procedural material from shader nodes: noise-driven color and displacement."""

import pyblender as pb

material = pb.Material()
noise = material.add_noise_texture(scale=5)
ramp = material.add_color_ramp(colors=["#FF0000", "#00FF00"])
height = material.add_math("MULTIPLY", value=0.1)

material.link(noise, ramp, "Fac", "Fac")
material.link(ramp, material.bsdf, "Color", "Base Color")
material.link(noise, height, "Fac", 0)
material.link(height, material.output, "Value", "Displacement")

pb.Cube(location=(0, -1, 0), material=material)
pb.Cube(location=(0, 1, 0), material=material)
pb.Sun(focus_point=(0, 0, 0))

camera = pb.Camera((10, 0, 0)).look_at((0, 0, 0))
scene = pb.Scene(camera)
scene.add_bloom()
scene.render("renders/node_material.png", fast=True)
