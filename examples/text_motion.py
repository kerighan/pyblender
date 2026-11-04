"""A title card: letters pop in one by one, a subtitle slides in, everything waves then leaves."""

import pyblender as pb
from pyblender import motion

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # any .ttf/.otf, None = built-in
N_FRAMES = 150

title = pb.Text("PYBLENDER", size=1.4, extrude=0.25, bevel=0.03, font=FONT, split="letters",
                tracking=0.04, material=pb.Material(color="#F7F7F2", roughness=0.35, metallic=0.1))
subtitle = pb.Text("motion text in 3D", size=0.45, extrude=0.05, font=FONT, split="words",
                   location=(0, 0, -0.9),
                   material=pb.Material(color="#FF6B35", emission_strength=1.5))

motion.pop_in(title, start=5, duration=18, stagger=3, easing="back-out")
motion.slide_in(subtitle, offset=(0, -0.6, 0), start=35, duration=15, stagger=6)
motion.wave(title, start=60, end=110, amplitude=0.12, period=25, phase=0.5)
motion.pop_out(title, start=115, duration=15, stagger=2, easing="back-in", reverse=True)
motion.slide_out(subtitle, offset=(0, -0.6, 0), start=120, duration=15, stagger=5)

# a dark backdrop and a warm key light with a cool rim
pb.Plane(size=60, location=(0, 4, 0), rotation=(1.5708, 0, 0),
         material=pb.Material(color="#14161C", roughness=0.9, metallic=0))
pb.Plane(size=60, location=(0, 0, -1.5),
         material=pb.Material(color="#14161C", roughness=0.6, metallic=0))
pb.SpotLight((4, -7, 6), focus_point=(0, 0, 0), energy=3000, color="#FFE2C4", angle=57, blend=0.5)
pb.PointLight((-6, -2, 3), energy=600, color="#7FB7FF", radius=1)

camera = pb.Camera((0, -11, 0.6), lens=50).look_at((0, 0, 0.2))
scene = pb.Scene(camera)
scene.add_bloom(intensity=0.04, radius=4, threshold=1.2)
scene.set_animation_bounds(0, N_FRAMES - 1)
scene.render("renders/text_motion.mp4", fast=True, size=(1280, 720), samples=32)
