import numpy as np
from pyblender import Camera, Cube, Material, PointLight, Scene, Sun
from pyblender.material import VolumeMaterial
from pyblender.utils import hex_to_rgba

FRAME_RATE = 24
DURATION = 6
N_FRAMES = DURATION * FRAME_RATE

COLORS = ["#96F7FE", "#532FD1", "#F94159", "#fcbd54", "#F916D7"]
POSITIONS = [.325, .513, .569, .616, .674]

# Sun()
# light = PointLight((-3, -1, 0), color="#facc77", energy=3000)

nebula_mat = VolumeMaterial(color="#FFFFFF")
musgrave = nebula_mat.create_musgrave_texture(
    detail=16, scale=-2, lacunarity=2.1, gain=25,
    noise_dimensions="4D",
    musgrave_type="RIDGED_MULTIFRACTAL",
    dimension=0)
musgrave.animate("W",
                 np.linspace(0, .01, N_FRAMES),
                 range(1, N_FRAMES+1))
noise = nebula_mat.create_noise_texture(
    noise_dimensions="4D", scale=10, detail=2, distortion=1)
noise.animate("W", np.linspace(0, .01, N_FRAMES),
              range(1, N_FRAMES+1))
color_ramp = nebula_mat.create_color_ramp(
    colors=COLORS, positions=POSITIONS, interpolation="EASE")
noise["Fac"].to(color_ramp["Fac"])
color_ramp[0].to(nebula_mat.bsdf["Color"])
color_ramp[0].to(nebula_mat.bsdf["Emission Color"])

map_range = nebula_mat.create_map_range(source=[1, 0], target=[-500, 20])
emission_op = nebula_mat.create_operation(operation="MULTIPLY", value=3.5)
density_op = nebula_mat.create_operation(operation="POWER", value=2.2)

# noise["Fac"].to(musgrave["Vector"])
musgrave["Fac"].to(map_range["Value"])
map_range["Result"].to(density_op["Value"])
density_op["Value"].to(nebula_mat.bsdf["Density"])
map_range["Result"].to(emission_op["Value"])
emission_op["Value"].to(nebula_mat.bsdf["Emission Strength"])

nebula = Cube(size=30, material=nebula_mat)
# nebula = Cube(size=25, location=(25, 0, 0), material=nebula_mat)


ys = (-8, -3)
xs = (-35, 10)
zs = (-5.7, -3.3)
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
# scene.set_animation_bounds(1, N_FRAMES)
scene.add_glare(
    size=1,
    saturation=1.15,
    contrast=1.1,
    dispersion=.001,
    gain=1.2)
scene.render("render.png",
             size=(1920//2, 1080//2),
             background_color="#040016",
             eevee=False,
             samples=64, frame=0,
             frame_rate=FRAME_RATE,
             contrast="Very High Contrast",
             volumetric_samples=256,
             volumetric_tile_size="2")
