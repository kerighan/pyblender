import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from pyblender import Box, Camera, Scene, camera
from pyblender.light import PointLight, Sun
from pyblender.material import EmissionMaterial, Material, RefractionBSDF
from pyblender.mesh import Model, merge_geometries

img = np.array(Image.open("Pac-Man.png"))

distinct_colors = set()
wall_set = set()
meeple_set = set()
map = np.zeros((21, 21), dtype=np.uint8)
for i in range(21):
    for j in range(21):
        cell = round(img[i*21:(i+1)*21, j*21:(j+1)*21].mean() / 7)
        distinct_colors.add(cell)
        if cell == 20:
            wall_set.add((i, j))
        elif 9 < cell < 12:
            meeple_set.add((i, j))
print(distinct_colors)


SIZE = .1
OFFSET = SIZE * 21 / 2
wall_mat = Material(emission_strength=11,
                    emission_color="#00605D",
                    roughness=.9,
                    color="#00605D")
walls = []
for (i, j) in wall_set:
    wall = Box(location=(i*SIZE - OFFSET, j*SIZE - OFFSET, 0),
               scale=(1, 1, .05), size=SIZE)
    walls.append(wall)
walls = merge_geometries(walls)
walls.add_material(wall_mat)
walls.modify_decimate("DISSOLVE")
walls.modify_wireframe(.007)


meeple_mat = Material(emission_color="#FFFFFF", emission_strength=13)
for (i, j) in meeple_set:
    meeple = Box(location=(i*SIZE - OFFSET, j*SIZE - OFFSET, 0),
                 scale=(1, 1, 1), size=.01,
                 material=meeple_mat)

x, y = -2, -3
pacman_mat = Material(color="#FDBF50",
                      roughness=.9,
                      # metallic=.9,
                      transmission=.7,
                      emission_strength=5)
# pacman = Model("pacman2.obj")
# pacman.set_material(material)
# pacman.translate(x * SIZE, y * SIZE, .01)
# pacman.scale(.1)
# pacman.rotate(0, 0, 90)
# pacman.modify_decimate("DISSOLVE")
# pacman.modify_wireframe()

camera = Camera((2, .5, 1.5))
camera.look_at((.1, 0, 0))
scene = Scene(cycles=True, size=(720, 720), samples=4096)

compositor = scene.create_compositor()
dirt = compositor.create_image("../astronaut/dirt.png")
glare = compositor.create_glare(size=8, mix=-.25)
mix = compositor.create_mix_rgb(fac=1, blend_type="MULTIPLY")
mix_2 = compositor.create_mix_rgb(fac=.9, blend_type="MIX")
distort = compositor.create_lens_distortion(distortion=.05, dispersion=.04)
cc = compositor.create_color_correction(contrast=1.,
                                        saturation=1.)
compositor.input["Image"].to(glare["Image"])
glare["Image"].to(mix[1])
dirt["Alpha"].to(mix[2])
compositor.input["Image"].to(mix_2[1])
mix["Image"].to(mix_2[2])
mix_2["Image"].to(distort["Image"])
distort["Image"].to(cc["Image"])
cc["Image"].to(compositor.output["Image"])


scene.render("render.png")
