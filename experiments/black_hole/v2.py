from experiments.materials import (create_black_hole_mat, create_sky_mat,
                                   create_smoke_mat)
from pyblender import Camera, Scene
from pyblender.light import PointLight, Sun
from pyblender.material import EmissionMaterial, Material, VolumeMaterial
from pyblender.mesh import Circle, Cylinder, IcoSphere, UVSphere

# create sky
sky = UVSphere(radius=200, location=(0, 0, 100), material=create_sky_mat())
sky.shade_smooth()

# create black hole
# black_hole = UVSphere(material=create_black_hole_mat(), radius=2, div=48)
# black_hole.shade_smooth()


# halo
# halo_mat = VolumeMaterial(density=.6)
# halo = UVSphere(location=(0, 0, 0), radius=2,
#                 material=halo_mat)
halo = UVSphere(location=(0, 0, 0), radius=10, scale=(1, 1, .1),
                material=create_smoke_mat())
halo.rotate(10, 10, 10)

camera = Camera((50, 0, 0), lens=150)
camera.look_at((0, 0, 0))
scene = Scene(camera)
# scene.add_bloom()
# scene.add_glare()
scene.render("render.png",
             use_ssr_refraction=True,
             eevee=True,
             size=(1920, 1080),
             samples=64,
             frame_rate=24)
