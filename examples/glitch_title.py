"""A sci-fi title card with screen glitches: text motion plus animated post-processing."""

import pyblender as pb
from pyblender import motion

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
N_FRAMES = 150

title = pb.Text("SYSTEM FAILURE", size=1.1, extrude=0.2, bevel=0.02, font=FONT, split="letters",
                material=pb.Material(color="#F0F4FF", roughness=0.3, emission_strength=0.4))
status = pb.Text("rebooting...", size=0.4, font=FONT, split="words", location=(0, 0, -0.9),
                 material=pb.Material(color="#2BFF88", emission_strength=3))
motion.flip_in(title, start=5, duration=12, stagger=2, easing="back-out")
motion.typewriter(status, start=45, stagger=8)
motion.shake(title, start=70, end=90, amplitude=0.06)
motion.pop_out(title, start=125, duration=10, stagger=1, easing="quint-in")
motion.slide_out(status, offset=(0, -0.5, 0), start=130, duration=12)

pb.Plane(size=60, location=(0, 4, 0), rotation=(1.5708, 0, 0),
         material=pb.Material(color="#0D1117", roughness=0.9, metallic=0))
pb.Plane(size=60, location=(0, 0, -1.5), material=pb.Material(color="#0D1117", roughness=0.4, metallic=0))
pb.SpotLight((3, -7, 5), focus_point=(0, 0, 0), energy=2500, color="#DDE8FF", size=1.0, blend=0.5)
pb.PointLight((-5, -3, 2), energy=400, color="#2BFF88", radius=1)

camera = pb.Camera((0, -11, 0.4), lens=50).look_at((0, 0, 0.1))
scene = pb.Scene(camera)
scene.set_animation_bounds(0, N_FRAMES - 1)

# post-processing: a CRT look all along, glitch bursts at key moments
post = scene.post
post.vignette(0.5)
post.scanlines(0.2, density=180)
post.glow(threshold=0.8, mix=0.2)
post.chromatic_aberration(0.02).animate("amount", [0.02, 0.5, 0.02], [70, 74, 80])
post.glitch(bursts=[(3, 14), (70, 82), (124, 132)], strength=1.0, seed=3)

scene.render("renders/glitch_title.mp4", fast=True, size=(1280, 720), samples=32)
