"""Matte, metallic and glass spheres on a color gradient. Cycles with depth of field."""

import pyblender as pb
from pyblender.animation import Timeline

N = 7
gradient = Timeline(0, 1)
gradient.color = [("linear", "#FF5E5B", "#3A86FF")]

rows = {
    1.5: dict(roughness=0.6, metallic=0.0),    # matte
    0.0: dict(roughness=0.15, metallic=1.0),   # metal
    -1.5: dict(roughness=0.05, metallic=0.0, opacity=0.15),  # glass
}
for y, params in rows.items():
    for i in range(N):
        color = gradient[i / (N - 1)].color
        pb.Sphere(location=(i - N / 2 + 0.5, y, 0.5), radius=0.45, div=64,
                  material=pb.Material(color=color, specular=0.5, **params))

pb.Plane(size=60, material=pb.Material(color="#E8E8E8", roughness=0.7, metallic=0))
pb.Sun(energy=3, focus_point=(0, 0, 0), location=(5, -5, 10))
pb.PointLight((-4, -6, 6), energy=1500, color="#FFF4E0", radius=2)

camera = pb.Camera((0, -11, 5), focus_point=(0, 0, 0.5), aperture_fstop=2.8, lens=50)
camera.look_at((0, 0, 0.3))
scene = pb.Scene(camera)
scene.render("renders/glass_spheres.png", fast=False, size=(1280, 720), samples=128)
