"""Fireflies drifting through fog under a spotlight: particles, turbulence and volumetric light."""

import pyblender as pb

N_FRAMES = 150

# a firefly is a tiny glowing sphere, stored far away and instanced by the particle system
firefly = pb.Sphere(location=(0, 0, 1000), radius=0.04, div=12,
                    material=pb.Material(color="#FFE066", emission_strength=40))
# the emitter itself is hidden at render time by the particle system
emitter = pb.Cube(location=(0, 0, 1.5), scale=(4, 4, 1.5))
pb.ParticleSystem(emitter, firefly, count=250, frames=(0, 1), lifetime=1000, size=1,
                  gravity=0, velocity_random=0.4, size_random=0.5, time_tweak=0.3)
pb.Turbulence(location=(0, 0, 1.5), strength=4, flow=1, noise=1)

# fog and ground
pb.Cube(location=(0, 0, 3), size=14, material=pb.VolumeMaterial(color="#9DB4C0", density=0.12))
pb.Plane(size=40, material=pb.Material(color="#1F2A1F", roughness=0.95, metallic=0))

# a single shaft of light from above
spot = pb.SpotLight((2, -2, 9), focus_point=(0, 0, 0), energy=3000, color="#CFE3FF",
                    size=0.6, blend=0.3, radius=0.5)
spot.animate_energy([3000, 2000, 3000], [0, N_FRAMES // 2, N_FRAMES])

camera = pb.Camera((7, -7, 2.2), lens=35).look_at((0, 0, 1.2))
scene = pb.Scene(camera)
scene.add_volumetric_light()
scene.add_bloom(intensity=0.1, radius=5, threshold=2)
scene.set_animation_bounds(0, N_FRAMES - 1)
scene.render("renders/fireflies.mp4", fast=True, size=(1280, 720), samples=32)
