"""Hundreds of cubes spiralling around a light, rendered as a looping video."""

import numpy as np
import pyblender as pb

N_FRAMES = 120
N_ROWS = 25
N_ARMS = 20
frames = range(N_FRAMES)


def circle(radius, phase):
    angles = np.linspace(0, 2 * np.pi, N_FRAMES, endpoint=False) + phase
    return [(radius * np.cos(a), radius * np.sin(a), 0) for a in angles]


camera = pb.Camera((10, 10, 10), focus_point=(2, 2, 2.5), aperture_fstop=0.1)
camera.look_at((0, 0, 0))
pb.PointLight((2, 2, 2.5), energy=80)

material = pb.Material()
for arm in np.linspace(0, 2 * np.pi, N_ARMS, endpoint=False):
    for i, radius in enumerate(np.linspace(0.2, 8, N_ROWS)):
        phase = np.pi * i / N_ROWS
        cube = pb.Cube(size=1.5 * (radius / N_ROWS) ** 0.7, material=material)
        cube.animate_location(circle(radius, arm + phase), frames)
        cube.animate_rotation_z(np.linspace(0, 720, N_FRAMES), frames)
        cube.animate_scale_z([3 * (2 - np.cos(3 * phase - t))
                              for t in np.linspace(0, 4 * np.pi, N_FRAMES)], frames)

scene = pb.Scene(camera)
scene.add_bloom(radius=10, intensity=0.5, threshold=0.6)
scene.set_animation_bounds(0, N_FRAMES - 1)
scene.render("renders/maelstrom.mp4", fast=False, size=(1000, 1000))
