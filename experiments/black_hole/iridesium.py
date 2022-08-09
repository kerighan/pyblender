from experiments.materials import (create_accretion_disk, create_black_hole,
                                   create_text_mat)
from pyblender import Camera, Scene
from pyblender.animation import linear, shake
from pyblender.light import PointLight, SpotLight
from pyblender.material import EmissionMaterial, Material, RefractionBSDF
from pyblender.mesh import Box, Cube, IcoSphere, Particles, Plane, Text

cam_location = (8, 0, 1.5)
cam_look_at = (0, .6, 0.24)
DURATION = 4

light = PointLight((1.1, -1, .4), energy=400, color="#851D58")
# light = PointLight((-1, 1, 1), energy=100, color="#B70001")

sphere = IcoSphere(material=create_black_hole(),
                   radius=1, location=(0, 0, 0))
sphere.shade_smooth()
sphere.set_cycles_visibility(diffuse=False, glossy=False,
                             transmission=False, scatter=False, shadow=False)

accretion_disk = Box(material=create_accretion_disk(), size=2)
accretion_disk.set_cycles_visibility(diffuse=True, glossy=False,
                                     transmission=True, scatter=True, shadow=False)
accretion_disk.resize(6, 6, .1)
accretion_disk.animate_rotation_z(
    *linear([0, 90*DURATION], [1, 24*DURATION+1]))

# text
text_material = create_text_mat()
R = Text("r", size=.2, extrude=.03,
         material=text_material,
         font="/home/maixent/fonts/Poppins-Bold.ttf")
R.rotate(0, 0, 90).rotate(0, 85, 0).rotate(5, 2, 0).translate(1.2, .1, .06)
E = Text("e", size=.2, extrude=.03,
         material=text_material,
         font="/home/maixent/fonts/Poppins-Bold.ttf")
E.rotate(0, 0, 90).rotate(0, 85, 0).rotate(-2, -5, -5).translate(1.1, .3, .05)
B = Text("b", size=.2, extrude=.03,
         material=text_material,
         font="/home/maixent/fonts/Poppins-Bold.ttf")
B.rotate(0, 0, 90).rotate(0, 85, 0).rotate(0, -1, 0).translate(.8, .5, .05)
O = Text("o", size=.2, extrude=.03,
         material=text_material,
         font="/home/maixent/fonts/Poppins-Bold.ttf")
O.rotate(0, 0, 90).rotate(0, 85, 0).rotate(1, 5, 0).translate(.25, .75, .03)
O = Text("o", size=.2, extrude=.03,
         material=text_material,
         font="/home/maixent/fonts/Poppins-Bold.ttf")
O.rotate(0, 0, 90).rotate(0, 85, 0).rotate(-1, 1, 0).translate(.6, .92, .06)
T = Text("t", size=.2, extrude=.03,
         material=text_material,
         font="/home/maixent/fonts/Poppins-Bold.ttf")
T.rotate(0, 0, 90).rotate(0, 85, 0).rotate(-3, 1, 0).translate(.65, 1.1, .1)


camera = Camera(location=cam_location, lens=150)
camera.look_at(cam_look_at)
# camera.animate_location(*shake([1, 48], cam_location,
#                                freq=.8, intensity=.002))

size = (1920, 1080)
scene = Scene(camera)
scene.add_glare(saturation=1.25)
scene.set_animation_bounds(1, 24*DURATION)
scene.render("render.png", eevee=False, samples=1500, size=size, frame=8,
             frame_rate=24, contrast="High Contrast", use_gtao=False)
