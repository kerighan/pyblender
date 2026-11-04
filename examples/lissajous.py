"""A glowing 3D Lissajous curve with lights racing along it, seen from an orbiting camera."""

import numpy as np
import pyblender as pb

N_FRAMES = 120
N_POINTS = 600
frames = range(N_FRAMES)

# the curve
u = np.linspace(0, 2 * np.pi, N_POINTS, endpoint=False)
points = [(3 * np.sin(3 * a), 3 * np.sin(2 * a), 2 * np.sin(5 * a)) for a in u]
curve = pb.Line(points + points[:1], stroke_width=0.03,
                material=pb.Material(color="#19D3FF", emission_strength=6))

# small lights racing along the curve, one loop per animation
runner_colors = ["#FF4D6D", "#FFD166", "#8AFF80"]
for k, color in enumerate(runner_colors):
    runner = pb.Sphere(radius=0.12, div=16, material=pb.Material(color=color, emission_strength=20))
    offset = k * N_POINTS // len(runner_colors)
    path = [points[(offset + f * N_POINTS // N_FRAMES) % N_POINTS] for f in frames]
    runner.animate_location(path, frames)

# the camera circles the curve while tracking its center
center = pb.Empty((0, 0, 0))
camera = pb.Camera((9, 0, 3), lens=40).look_at(center)
orbit = np.linspace(0, 2 * np.pi, N_FRAMES, endpoint=False)
camera.animate_location([(9 * np.cos(a), 9 * np.sin(a), 3 + np.sin(2 * a)) for a in orbit], frames)

scene = pb.Scene(camera)
scene.add_bloom(intensity=0.08, radius=6, threshold=1)
scene.set_animation_bounds(0, N_FRAMES - 1)
scene.render("renders/lissajous.mp4", fast=True, size=(1280, 720), samples=32)
