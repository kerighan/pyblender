"""A field of cubes rippling like water. The animation loops seamlessly."""

import numpy as np
import pyblender as pb

N = 24
N_FRAMES = 90
frames = range(N_FRAMES)
t = np.linspace(0, 2 * np.pi, N_FRAMES, endpoint=False)

material = pb.Material(color="#2A6FDB", roughness=0.25, metallic=0.3)
for i in range(N):
    for j in range(N):
        x, y = i - N / 2 + 0.5, j - N / 2 + 0.5
        phase = 0.7 * np.hypot(x, y)
        heights = 1 + 0.8 * np.sin(t - phase)
        cube = pb.Cube(location=(x, y, 0), scale=(0.85, 0.85, 1), material=material)
        cube.animate_scale_z(heights, frames)
        cube.animate_location([(x, y, h / 2) for h in heights], frames)

pb.Plane(size=200, location=(0, 0, -0.01), material=pb.Material(color="#0B1626", roughness=0.9))
pb.Sun(energy=4, focus_point=(0, 0, 0), location=(10, -20, 30))
pb.PointLight((0, 0, 12), energy=4000, color="#FFD9A0", radius=3)

camera = pb.Camera((N * 0.9, -N * 0.9, N * 0.6), lens=45).look_at((0, 0, 0))
scene = pb.Scene(camera)
scene.set_animation_bounds(0, N_FRAMES - 1)
scene.render("renders/wave_grid.mp4", fast=True, size=(1280, 720), samples=32)
