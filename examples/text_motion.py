"""A title card: letters pop in one by one, a subtitle slides in, everything waves then leaves."""

import pyblender as pb

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # any .ttf/.otf, None = built-in

title = pb.Text("PYBLENDER", size=1.4, extrude=0.25, bevel=0.03, font=FONT, split="letters",
                tracking=0.04, material=pb.Material(color="#F7F7F2", roughness=0.35, metallic=0.1))
subtitle = pb.Text("motion text in 3D", size=0.45, extrude=0.05, font=FONT, split="words",
                   location=(0, 0, -0.9),
                   material=pb.Material(color="#FF6B35", emission_strength=1.5))

# each group has its own playhead (in seconds): motions chain, wait() leaves a pause
title.parts.wait(0.2).pop_in(duration=0.6, stagger=0.1).wait(0.3).wave(duration=1.7, amplitude=0.12)
title.parts.wait(0.2).pop_out(duration=0.5, stagger=0.07, reverse=True)
subtitle.parts.wait(1.2).slide_in(offset=(0, -0.6, 0), duration=0.5, stagger=0.2)
subtitle.parts.wait(1.5).slide_out(offset=(0, -0.6, 0), duration=0.5, stagger=0.15)

# a dark backdrop and a warm key light with a cool rim
pb.Plane(size=60, location=(0, 4, 0), rotation=(90, 0, 0), material="#14161C")
pb.Plane(size=60, location=(0, 0, -1.5), material=pb.Material(color="#14161C", roughness=0.6))
pb.SpotLight((4, -7, 6), target=(0, 0, 0), energy=3000, color="#FFE2C4", angle=57, blend=0.5)
pb.PointLight((-6, -2, 3), energy=600, color="#7FB7FF", radius=1)
pb.Camera((0, -11, 0.6), target=(0, 0, 0.2), lens=50)

pb.scene().add_bloom(intensity=0.04, radius=4, threshold=1.2)
pb.render("renders/text_motion.mp4", duration=5, size=(1280, 720), samples=32)
