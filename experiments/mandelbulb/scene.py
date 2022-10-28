from pyblender.mesh import Box, Plane
from pyblender.light import Sun, PointLight
from pyblender.material import Material
from pyblender import Scene, Camera
from fractal import get_fractal, DURATION, N_FRAMES


def add_effects(scene):
    compositor = scene.create_compositor()
    
    glare = compositor.create_glare(size=8, mix=1)
    distort = compositor.create_lens_distortion(distortion=.0, dispersion=.03)
    cc = compositor.create_color_correction(contrast=1.,
                                            saturation=1.03)

    compositor.input["Image"].to(glare["Image"])
    glare["Image"].to(distort["Image"])
    distort["Image"].to(cc["Image"])
    cc["Image"].to(compositor.output["Image"])


# Sun()

left = PointLight((1, 2, 0))
right = PointLight((1, -2, 0))

fractal = get_fractal(512)
plane = Plane(size=10, material=Material(color="#161513"))
plane.rotate(0, 90, 0)
plane.translate(-4, 0, 0)

camera = Camera((4, 0, 0), use_dof=True, aperture_fstop=.5,
                focus_point=(1, 0, 0))
camera.look_at((1, 0, 0))
scene = Scene(size=(720, 720), cycles=False)
scene.set_animation_bounds(1, N_FRAMES)
# add_effects(scene)
scene.render("render.png", samples=256, frame=75)
