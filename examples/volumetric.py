import pyblender

cube_mat = pyblender.VolumeMaterial(color="#FFFFFF", density=.1)
cube = pyblender.Cube((0, 0, 0), rotation=(0, 0, .7),
                      size=10, material=cube_mat)


sphere_mat = pyblender.Material(color="#FFFFFF")
sphere = pyblender.Sphere((0, 0, 0), radius=.3, material=sphere_mat, div=256)

light = pyblender.SpotLight((2, 2, 2), focus_point=(0, 0, 0), energy=2000,
                            color="#6ACEFB",
                            attenuation=.1, blend=.15, size=.3)

camera = pyblender.camera.Camera((4, 0, 0), use_dof=False)
camera.look_at((0, 0, 0))
scene = pyblender.Scene(camera)
# scene.set_animation_bounds(0, 100)
scene.render("volumetric.png", fast=False, size=(1920, 1080))
