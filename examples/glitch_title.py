"""A sci-fi title card with screen glitches: text motion plus animated post-processing."""

import pyblender as pb

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

title = pb.Text("SYSTEM FAILURE", size=1.1, extrude=0.2, bevel=0.02, font=FONT, split="letters",
                material=pb.Material(color="#F0F4FF", roughness=0.3, emission_strength=0.4))
status = pb.Text("rebooting...", size=0.4, font=FONT, split="words", location=(0, 0, -0.9),
                 material=pb.Material(color="#2BFF88", emission_strength=3))

title.parts.wait(0.2).flip_in(duration=0.4, stagger=0.07)
title.parts.wait(1.3).shake(amplitude=0.06, duration=0.7)
title.parts.wait(1.2).pop_out(duration=0.3, stagger=0.03, easing="quint-in")
status.parts.wait(1.5).typewriter(stagger=0.25)
status.parts.wait(2.3).slide_out(offset=(0, -0.5, 0), duration=0.4)

pb.Plane(size=60, location=(0, 4, 0), rotation=(90, 0, 0), material="#0D1117")
pb.Plane(size=60, location=(0, 0, -1.5), material=pb.Material(color="#0D1117", roughness=0.4))
pb.SpotLight((3, -7, 5), target=(0, 0, 0), energy=2500, color="#DDE8FF", angle=57, blend=0.5)
pb.PointLight((-5, -3, 2), energy=400, color="#2BFF88", radius=1)
pb.Camera((0, -11, 0.4), target=(0, 0, 0.1), lens=50)

# post-processing: a CRT look all along, glitch bursts at key moments
pb.post.vignette(0.5)
pb.post.scanlines(0.2, density=180)
pb.post.glow(threshold=0.8, mix=0.2)
pb.post.chromatic_aberration(0.02).animate("amount", [0.02, 0.5, 0.02], [70, 74, 80])  # raw frames
pb.post.glitch(bursts=[(0.1, 0.5), (2.3, 2.7), (4.1, 4.4)], strength=1.0, seed=3)      # seconds

pb.render("renders/glitch_title.mp4", duration=5, size=(1280, 720), samples=32)
