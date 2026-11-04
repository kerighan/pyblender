"""Particles blown by turbulence inside a fog volume, with a fading light."""

import pyblender as pb

DURATION = 6 * 60  # frames

particle = pb.Cube(location=(1000, 1000, 1000), size=0.5, material=pb.Material())
emitter = pb.IcoSphere(radius=0.05)
pb.ParticleSystem(emitter, particle, count=500, frames=(-1, 1), lifetime=800, gravity=0,
                  velocity_random=5, size_random=0.3, phase_random=1, rotation_random=1,
                  angular_velocity=1, time_tweak=0.15)
pb.Turbulence(strength=50, flow=10)

pb.Cube(size=10, material=pb.VolumeMaterial(density=0.5))
light = pb.PointLight((0, 0, 0), energy=20)
light.animate_energy([22, 12, 0], [0, 5 * 60, DURATION])

camera = pb.Camera((5, 0, 0)).look_at((0, 0, 0))
scene = pb.Scene(camera)
scene.set_animation_bounds(0, DURATION)
scene.render("renders/particles.mp4", size=(900, 900), fast=True, frame_rate=60)
