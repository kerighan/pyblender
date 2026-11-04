"""Build a procedural material from shader nodes: noise-driven color and displacement.

Sockets are attributes, ``>>`` links them and arithmetic creates Math nodes.
"""

import pyblender as pb

material = pb.Material(roughness=0.4)
noise = material.create_noise_texture(scale=5)
ramp = material.create_color_ramp(colors=["#FF0000", "#00FF00"])

noise.fac >> ramp.fac >> material.bsdf.base_color
(noise.fac * 0.1) >> material.output.displacement

pb.Cube(location=(0, -1, 0), material=material)
pb.Cube(location=(0, 1, 0), material=material)
pb.Sun(focus_point=(0, 0, 0))

camera = pb.Camera((10, 0, 0)).look_at((0, 0, 0))
scene = pb.Scene(camera)
scene.add_bloom()
scene.render("renders/node_material.png", fast=True)
