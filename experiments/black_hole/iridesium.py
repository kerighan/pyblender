from pyblender.material import EmissionMaterial, Material
from pyblender.mesh import Cube, IcoSphere, Particles, Plane, Box
from pyblender import Camera, Scene
from pyblender.light import SpotLight
from pyblender.animation import linear, shake
from experiments.materials import create_black_hole, create_accretion_disk, create_dust_disk

cam_location = (8, 0, 1.8)
cam_look_at = (0, .6, 0.25)


red_light = SpotLight((-3, 1, 2), energy=200, color="#FEFE71", angle=20)
red_light.look_at(cam_location)
# red_light = PointLight((-3, 1, 2), energy=2000, color="#FF0000")


sphere = IcoSphere(material=create_black_hole())
sphere.shade_smooth()
sphere.set_cycles_visibility(diffuse=False, glossy=False,
                             transmission=False, scatter=False, shadow=False)

accretion_disk = Box(material=create_accretion_disk(), size=2)
accretion_disk.resize(5, 5, .1)
accretion_disk.animate_rotation_z(*linear([0, 180], [1, 48]))

# dust_disk = Box(location=(0, 0, .25), material=create_dust_disk(), size=2)
# dust_disk.resize(5, 5, .1)

# asteroid_cloud = Box(location=(0, 0, 0), size=2)
# asteroid_cloud.resize(5, 5, .1)
# asteroid = IcoSphere(radius=.1, material=EmissionMaterial())
# asteroid.set_visible(False)
# particles = Particles(asteroid_cloud, asteroid,
#                       gravity=0,
#                       count=500,
#                       size_random=.9, frames=[0, 0])
# Vortex()

camera = Camera(location=cam_location, lens=150)
camera.look_at(cam_look_at)
camera.animate_location(*shake([1, 48], cam_location,
                               freq=.8, intensity=.003))


size = (1920//2, 1080//2)
scene = Scene(camera)
scene.add_glare()
scene.set_animation_bounds(1, 48)
scene.render("render.mp4", eevee=False, samples=16, size=size, frame_rate=24)
