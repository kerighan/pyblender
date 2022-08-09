import numpy as np
from experiments.materials import create_sky_mat
from pyblender import Camera, Cube, Material, PointLight, Scene, Sun
from pyblender.material import EmissionMaterial, RefractionBSDF, VolumeMaterial
from pyblender.mesh import Text, UVSphere
from pyblender.utils import hex_to_rgba

# create sky
sky = UVSphere(radius=200, location=(0, 0, 100), material=create_sky_mat())
sky.shade_smooth()

FRAME_RATE = 24
DURATION = 8
N_FRAMES = DURATION * FRAME_RATE

COLORS = ["#96F7FE", "#532FD1", "#F94159", "#fcbd54", "#F916D7"]
POSITIONS = [.325, .513, .569, .616, .674]

xs = (-40, 13)
ys = (-6, -6.2)
zs = (-.5, -2.8)
# Sun()
# light = PointLight((-3, -1, 0), color="#facc77", energy=3000)
font = "/home/maixent/fonts/Poppins-Medium.ttf"

text_material = EmissionMaterial("#FFFFFF", emission_strength=6)
r = Text("r", size=.15, extrude=.02, material=text_material, font=font)
r.rotate(0, 0, -90).rotate(0, -90, 0).rotate(-5, 8, 0)
r.translate(-34.7, -6.4, -1)
e = Text("e", size=.15, extrude=.02, material=text_material, font=font)
e.rotate(0, 0, -90).rotate(0, -90, 0).rotate(10, 5, 0)
e.translate(-29.7, -5.8, -.7)
b = Text("b", size=.15, extrude=.02, material=text_material, font=font)
b.rotate(0, 0, -90).rotate(0, -90, 0).rotate(-10, 5, 0)
b.translate(-26.7, -6.1, -1.1)
o = Text("o", size=.15, extrude=.02, material=text_material, font=font)
o.rotate(0, 0, -90).rotate(0, -90, 0).rotate(4, -9, 1)
o.translate(-21.7, -6.5, -.8)
o = Text("o", size=.15, extrude=.02, material=text_material, font=font)
o.rotate(0, 0, -90).rotate(0, -90, 0).rotate(9, -9, 1)
o.translate(-18.7, -6., -1.2)
t = Text("t", size=.15, extrude=.02, material=text_material, font=font)
t.rotate(0, 0, -90).rotate(0, -90, 0).rotate(-4, -4, -1)
t.translate(-10.7, -6., -1.6)

nebula_mat = VolumeMaterial(color="#FFFFFF")
musgrave = nebula_mat.create_musgrave_texture(
    detail=16, scale=-3, lacunarity=2.1, gain=25,
    noise_dimensions="4D",
    musgrave_type="RIDGED_MULTIFRACTAL",
    dimension=0)
musgrave.animate("W",
                 np.linspace(0, .01, N_FRAMES),
                 range(1, N_FRAMES+1))
noise = nebula_mat.create_noise_texture(
    noise_dimensions="4D", scale=4, detail=2, distortion=1)
noise.animate("W", np.linspace(0, .01, N_FRAMES),
              range(1, N_FRAMES+1))
color_ramp = nebula_mat.create_color_ramp(
    colors=COLORS, positions=POSITIONS, interpolation="EASE")
noise["Fac"].to(color_ramp["Fac"])
color_ramp[0].to(nebula_mat.bsdf["Color"])
color_ramp[0].to(nebula_mat.bsdf["Emission Color"])

map_range = nebula_mat.create_map_range(source=[1, 0], target=[-500, 15])
emission_op = nebula_mat.create_operation(operation="MULTIPLY", value=2)
density_op = nebula_mat.create_operation(operation="POWER", value=2.2)

# noise["Fac"].to(musgrave["Vector"])
musgrave["Fac"].to(map_range["Value"])
map_range["Result"].to(density_op["Value"])
density_op["Value"].to(nebula_mat.bsdf["Density"])
map_range["Result"].to(emission_op["Value"])
emission_op["Value"].to(nebula_mat.bsdf["Emission Strength"])

nebula = Cube(size=30, material=nebula_mat)
# nebula = Cube(size=25, location=(25, 0, 0), material=nebula_mat)


# from -3 to
camera = Camera((-1, ys[0], zs[0]), lens=50)
camera.look_at((100, ys[0], zs[0]))

locations = [(x, y, z) for x, y, z in zip(
    np.linspace(xs[0], xs[1], N_FRAMES),
    np.linspace(ys[0], ys[1], N_FRAMES),
    np.linspace(zs[0], zs[1], N_FRAMES))]
camera.animate_location(locations,
                        range(1, N_FRAMES+1))


scene = Scene(camera)
scene.set_animation_bounds(1, N_FRAMES)
scene.add_glare(
    size=3,
    saturation=1.15,
    contrast=1.1,
    dispersion=.001,
    gain=1.2)
scene.render("render.mp4",
             size=(1920, 1080),
             background_color="#000000",
             eevee=False,
             samples=100, frame=int(24*.0),
             frame_rate=FRAME_RATE,
             contrast="Very High Contrast",
             volumetric_samples=256,
             volumetric_tile_size="2")
