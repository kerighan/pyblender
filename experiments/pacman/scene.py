import numpy as np
from PIL import Image
from pyblender import Box, Camera, Scene, camera
from pyblender.light import PointLight, Sun
from pyblender.material import EmissionMaterial, Material, RefractionBSDF
from pyblender.mesh import Model, UVSphere, merge_geometries
from pyblender.animation import Movement
from pyblender.utils import hex_to_rgb
# sys.path.insert(1, 'models.py')
# spec = importlib.util.spec_from_file_location(
#     "models", "models.py")
# models = importlib.util.module_from_spec(spec)
from models import create_pacman, create_ghosts, create_ground

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


SIZE = .1
OFFSET = SIZE * 21 / 2
create_ground()

PointLight((0, -OFFSET, .12), color="#00605D", energy=20)
PointLight((0, OFFSET, .12), color="#00605D")

# create pacman
movement = create_pacman()
dates_of_death = {}
for t, frame in enumerate(movement.frames):
    frame += OFFSET
    frame /= SIZE
    i, j = frame[:2]
    if np.abs(i - int(i)) < .2 and np.abs(j - int(j)) < .2:
        i, j = int(round(i)), int(round(j))
        if (i, j) not in dates_of_death:
            dates_of_death[i, j] = t


# ghosts
create_ghosts(movement.duration)

# meeples
meeples = {}
meeple_mat = Material(emission_color="#FBF2E9", emission_strength=10)
for (i, j) in meeple_set:
    meeple = Box(location=(i*SIZE - OFFSET, j*SIZE - OFFSET, 0.01),
                 scale=(1, 1, 1), size=.008,
                 material=meeple_mat)
    if (i, j) in dates_of_death:
        t = dates_of_death[i, j]
        meeple.animate_visibility([False, True], [t, t+1])
    meeples[i, j] = meeple

intensity = meeple_mat.create_value(value=11)
intensity[0].to(meeple_mat.bsdf["Emission Strength"])
intensity.animate_internal([10, 0], [113, 124])

# walls
wall_mat = Material(emission_strength=15,
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
walls.modify_wireframe(.005)
# animate walls
intensity = wall_mat.create_value(value=13)
noise = wall_mat.create_noise_texture(scale=5)
multiply = wall_mat.create_operation()
multiply[0].to(wall_mat.bsdf["Emission Strength"])
noise[0].to(multiply[0])
intensity[0].to(multiply[1])

# intensity[0].to(wall_mat.bsdf["Emission Strength"])
intensity.animate_internal([13, 0], [120, 131])


camera = Camera((2, .5, 1.5))
camera.look_at((.12, 0, 0))


scene = Scene(cycles=True, size=(720, 720), samples=1024)
scene.set_animation_bounds(1, 140)

compositor = scene.create_compositor()
dirt = compositor.create_image("dirt.png")
glare = compositor.create_glare(size=7, mix=1)
mix = compositor.create_mix_rgb(fac=1, blend_type="MULTIPLY")
mix_2 = compositor.create_mix_rgb(fac=.6, blend_type="MIX")
distort = compositor.create_lens_distortion(distortion=.0, dispersion=.03)
cc = compositor.create_color_correction(contrast=1.,
                                        saturation=1.03)
compositor.input["Image"].to(glare["Image"])
glare["Image"].to(mix[1])
dirt["Alpha"].to(mix[2])
compositor.input["Image"].to(mix_2[1])
mix["Image"].to(mix_2[2])
mix_2["Image"].to(distort["Image"])
distort["Image"].to(cc["Image"])
cc["Image"].to(compositor.output["Image"])

# print(movement.duration)
scene.render("render.mp4", frame=5)
