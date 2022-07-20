from math import radians

from pyblender import Camera, Scene
from pyblender.light import PointLight, Sun
from pyblender.material import Material
from pyblender.mesh import Box, Grid, Plane
from pyblender.utils import hex_to_rgba

# Sun()
PointLight((0, 0, 0))
DURATION = 16
FRAME_RATE = 60


def create_mat(color, color_2):
    mat = Material(
        roughness=1,
        emission_strength=20,
        emission_color=color,
        color=color)
    mat.bsdf["Subsurface IOR"] = 1.01

    # first one
    mapping = mat.create_mapping()
    texcoord = mat.create_texture_coordinate()
    wave = mat.create_wave_texture(
        wave_type="RINGS", wave_profile="TRI",
        scale=.1, distortion=5.7, detail=9)
    noise = mat.create_musgrave_texture(
        scale=3.5, detail=12, dimension=25.7, offset=.05,
        musgrave_type="HYBRID_MULTIFRACTAL")
    magic = mat.create_magic_texture(distortion=-6.1)
    cr = mat.create_color_ramp(positions=[.7, 1])
    mix_shader = mat.create_mix_shader()

    mapping["Scale"] = (-1.3, -.7, .8)
    texcoord["Generated"].to(mapping["Vector"])
    mapping["Vector"].to(wave["Vector"])
    wave["Color"].to(noise["Vector"])
    noise[0].to(magic["Vector"])
    magic["Color"].to(cr["Fac"])
    cr["Color"].to(mat.bsdf["Alpha"])

    # second one
    mapping = mat.create_mapping()
    texcoord = mat.create_texture_coordinate()
    brick = mat.create_brick_texture(scale=1.8)
    add = mat.create_operation(operation="ADD", value=.15)
    magic = mat.create_magic_texture(
        distortion=-5.1)
    cr2 = mat.create_color_ramp(positions=[.8, 1])
    bsdf = mat.create_principled_bsdf()
    bsdf["Base Color"] = hex_to_rgba(color_2)
    bsdf["Roughness"] = 1

    mapping["Rotation"] = (radians(7), radians(-16), radians(10))
    mapping["Scale"] = (-50, 200, 40)
    bsdf["Emission Strength"] = 25
    bsdf["Emission"] = hex_to_rgba(color_2)
    # bsdf["Roughness"] = 0
    texcoord["Generated"].to(mapping["Vector"])
    mapping["Vector"].to(brick["Vector"])
    brick["Color"].to(add["Value"])
    add["Value"].to(cr2["Fac"])
    cr2["Color"].to(bsdf["Alpha"])
    bsdf[0].to(mix_shader[2])
    mat.bsdf[0].to(mix_shader[1])

    mix_shader[0].to(mat.material_output["Surface"])

    return mat


size = 400
box_left = Box(location=(-size/2+1, -.4, 0),
               scale=(size, .01, 10),
               material=create_mat("#0014FC", "#FF0101"))
box_right = Box(location=(-size/2+1, .4, 0),
                scale=(size, .01, 10),
                material=create_mat("#FF0101", "#0014FC"))

camera = Camera(location=(1, 0, 0), lens=14)
camera.look_at((0, 0, 0))
camera.animate_location(
    [(1, 0, 0), (-size // 2, 0, 0)], [1, FRAME_RATE*DURATION])
camera.animate_rotation(
    [(radians(90), radians(-20), radians(90)),
     (radians(90), radians(110), radians(90))], [1, FRAME_RATE*DURATION])
scene = Scene(camera)
scene.add_bloom(radius=6, intensity=.01, threshold=.9)
# scene.add_glare()
scene.set_animation_bounds(1, FRAME_RATE*DURATION)
scene.render(
    "render.mp4", size=(1920, 1080), samples=64, eevee=True,
    contrast="Very High Contrast", frame_rate=FRAME_RATE)
