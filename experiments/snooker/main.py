import numpy as np
from pyblender import Camera, Scene
from pyblender.light import PointLight, SpotLight, Sun
from pyblender.material import Material
from pyblender.mesh import Cube, Particles, Plane, UVSphere
from pyblender.texture import Image

np.random.seed(0)

light = SpotLight((.5, 0, .5), color="#D8654E")
light.look_at((0, 0, 0))

BALL_RADIUS = 0.052

carpet = Material(
    color="#00605D", displace=False, bump=True, roughness=.6)
magic_texture = carpet.create_noise_texture(
    scale=8000, detail=512, distortion=0.2)
add = carpet.create_operation("ADD")
multiply2 = carpet.create_operation("MULTIPLY", value=.1)
cr = carpet.create_color_ramp(colors=["#000000", "#0000FF"])
magic_texture["Color"].to(multiply2[0])
multiply2[0].to(cr["Fac"])
cr["Color"].to(carpet.material_output["Displacement"])

board = Plane(material=carpet, size=10, location=(0, 0, 0))
board.obj.cycles.use_adaptive_subdivision = True
board.modify_subdivide(subdivision_type="SIMPLE")
board.modify_rigid_body("PASSIVE")
# board.modify_collision()

# SKIN BALL
skin = Material(subsurface=.7, bump=True, roughness=0.55)
texture = skin.create_texture(Image("textures/skin.jpg"))
normal = skin.create_texture(Image("textures/NormalMap.png"))
displacement = skin.create_texture(Image("textures/DisplacementMap.png"))
texture["Color"].to(skin.bsdf["Base Color"])
# normal["Color"].to(skin.bsdf["Normal"])
displacement["Color"].to(skin.material_output["Displacement"])

fur = Material(color="#232323")
fur_dark = Material(color="#000000")


def create_ball(location, rotation):
    skin_ball = UVSphere(radius=BALL_RADIUS,
                         location=location,
                         material=skin,
                         rotation=rotation)
    skin_ball.modify_rigid_body(
        friction=.05, mass=1, restitution=0, linear_damping=.01)
    skin_ball.add_material(fur)
    hair = Particles(
        skin_ball, None, hair=True, count=8, gravity=1,
        size_random=0, hair_length=0.01, emit_from="FACE", hair_step=5, clump_factor=.0, hide_emitter=False, length_random=0.5,
        frames=[-50, 100], material=2,
        effect_hair=.6, child_type="INTERPOLATED",
        clump_shape=0, root_radius=.03)
    skin_ball.shade_smooth()


F = 3**.5 + 5e-1
create_ball((0, 0, BALL_RADIUS), (0, 0, 0))
create_ball((-BALL_RADIUS*F, -BALL_RADIUS*F/1.8, BALL_RADIUS),
            (-60, 50, 5))
create_ball((-BALL_RADIUS*F, BALL_RADIUS*F/1.8, BALL_RADIUS),
            (24, 0, 45))


fur_ball = UVSphere(radius=BALL_RADIUS, material=skin,
                    location=(.5, 0, BALL_RADIUS))
fur_ball.modify_rigid_body(friction=.1, restitution=0,
                           linear_damping=.95, mass=1)
fur_ball.throw((-.2, 0, 0), frame_start=18)

fur_ball.add_material(fur)
hair = Particles(fur_ball, None, hair=True, count=75, gravity=1,
                 size_random=0, hair_length=0.03, emit_from="FACE", hair_step=5, clump_factor=0, hide_emitter=False, length_random=0.9, frames=[-50, 100], material=2,
                 effect_hair=.4, child_type="INTERPOLATED", clump_shape=0, root_radius=.04)
fur_ball.shade_smooth()


mega_ball = UVSphere(radius=BALL_RADIUS,
                     material=skin,
                     location=(0, -0.6, BALL_RADIUS))
mega_ball.modify_rigid_body(friction=.1, restitution=0,
                            linear_damping=.95, mass=1)
mega_ball.throw((0, 0.3, 0), frame_start=126)

mega_ball.add_material(fur)
hair = Particles(mega_ball, None, hair=True, count=300, gravity=1,
                 size_random=0, hair_length=0.05, emit_from="FACE", hair_step=5, clump_factor=0, hide_emitter=False, length_random=0.9, frames=[-50, 100], material=2,
                 effect_hair=.4, child_type="INTERPOLATED", clump_shape=0, root_radius=.04)
mega_ball.shade_smooth()

camera = Camera((.35, -.35, .2))
camera.look_at((0, 0, 0.04))
scene = Scene(size=(720, 720), cycles=True, samples=1024)
# scene = Scene(size=(400, 400), cycles=True, samples=32)
scene.set_animation_bounds(1, 232)
scene.render("render.mp4")
# scene.add_glare(saturation=1.1, gain=1.05, dispersion=.02)
# scene.render("render.png", frame=30)
