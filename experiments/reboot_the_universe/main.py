from math import radians

# from experiments.nebula.main import N_FRAMES
from pyblender import Camera, Scene
from pyblender.force import Turbulence
from pyblender.light import PointLight, SpotLight, Sun
from pyblender.material import (EmissionMaterial, Material, RefractionBSDF,
                                VolumeMaterial)
from pyblender.mesh import Cube, Particles, Text, UVSphere

FRAME_RATE = 24
light_left = PointLight((.25, 4, 0), color="#F916D7", energy=500)
light_right = PointLight((.25, -4, 0), color="#009CF8", energy=500)
light_left.animate_energy([0, 500], [0, FRAME_RATE])
light_right.animate_energy([0, 500], [0, FRAME_RATE])

flash = SpotLight((-10, 0, 0), energy=10000, color="#F94159")
flash.look_at((0, 0, 0))
flash.animate_energy([0, 10000], [0, 2*FRAME_RATE])
# flash.animate_energy(
#     [0, 0, 10000, 0],
#     (0, 2*FRAME_RATE-1, FRAME_RATE, FRAME_RATE + 10))

# light = SpotLight((3, 1, 0), angle=45, color="#FF0F02", energy=4000)
# light.look_at((0, 1, 0))
# light = SpotLight((3, -1, 0), angle=45, color="#009CF8", energy=4000)
# light.look_at((0, -1, 0))


# mat = EmissionMaterial(emission_strength=50, color="#F94159")
# sphere = UVSphere(location=(-2, 0, 0), scale=(1, 1, .02),
#                   radius=2, material=mat)
# cube = Cube(size=.3, material=mat)
# cube.set_visible(False)

mat = Material()
text = Text("reboot", size=2, extrude=.2, material=mat,
            font="/home/maixent/fonts/Poppins-Bold.ttf")
text.rotate(0, 0, 90)
text.rotate(0, 90, 0)
text.convert_to_mesh()
text.modify_remesh(mode="SMOOTH",
                   remove_disconnected=False,
                   octree_depth=8, smooth_shade=True)


particles = Particles(text, None, hide_emitter=False, size=.1,
                      count=30000, lifetime=120, velocity=0, gravity=0,
                      frames=(2*FRAME_RATE, 2*FRAME_RATE), time_tweak=1.5,
                      rotation_factor_random=.15, use_modifier_stack=True)
text.modify_explode(edge_cut=True)

Turbulence(strength=25, size=1, flow=3)

camera = Camera((10, 0, 0), lens=50, use_dof=True, focus_point=(0, 0, 0),
                aperture_ratio=1, aperture_fstop=.15)
camera.look_at((0, 0, 0))
camera.animate_location([(19, 0, 0), (10, 0, 0), (0, 0, 0)], [
                        1, FRAME_RATE*3, FRAME_RATE*4])

scene = Scene(camera)
scene.add_glare()
scene.set_animation_bounds(1, FRAME_RATE*4)
# scene.render("render.png", (800, 800), frame_rate=FRAME_RATE, eevee=False)
scene.render("render.mp4", (1920, 1080),
             frame_rate=FRAME_RATE, eevee=False, samples=512)
