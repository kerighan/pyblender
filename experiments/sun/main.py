from experiments.materials import create_sun_mat
from pyblender import Camera, Scene
from pyblender.light import Sun
from pyblender.mesh import IcoSphere

DURATION = 4
cam_location = (20, 0, 0)
cam_look_at = (0, 0, 0)

Sun()
sun = IcoSphere(material=create_sun_mat())

camera = Camera(location=cam_location, lens=150)
camera.look_at(cam_look_at)
# camera.animate_location(*shake([1, 48], cam_location,
#                                freq=.8, intensity=.002))

size = (1920, 1080)
scene = Scene(camera)
scene.add_glare(saturation=1.25)
scene.set_animation_bounds(1, 24*DURATION)
scene.render("render.png", eevee=False, samples=64, size=size,
             frame_rate=24, contrast="High Contrast")
