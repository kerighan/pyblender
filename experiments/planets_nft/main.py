from experiments.planets_nft.material import (create_atmosphere_material,
                                              create_clouds_material,
                                              create_planet_material)
from pyblender import Camera, Scene
from pyblender.light import PointLight, Sun
from pyblender.material import Material
from pyblender.mesh import IcoSphere, UVSphere
from pyblender.texture import Image, Noise
from pyblender.utils import hex_to_rgba

# HEIGHT_THRESHOLD = .5
HEIGHT = 1
SIZE = 5
TEXTURE = "MUSGRVE"
COLORS = ["#AFCBFF", "#FFEDE1"]

# Sun(location=(10, 10, 0))
PointLight((2, -1, 1.5), energy=600, color="#EDD8B2")
PointLight((-1, 1, -1.5), energy=200, color="#EDD8B2")

image = Image("img/mercury.jpg")


planet = UVSphere(material=create_planet_material(),
                  rotation=(0, 0, 0), div=64)
planet.shade_smooth()

clouds = UVSphere(material=create_clouds_material(),
                  rotation=(0, 0, 0), div=64, radius=1.005)
clouds.shade_smooth()

atmosphere = UVSphere(material=create_atmosphere_material(),
                      rotation=(0, 0, 0), div=64, radius=2)

camera = Camera((6, 6, 4), lens=100)
camera.look_at((0, 0, 0))
scene = Scene(camera)
scene.add_glare(saturation=1.2, gain=1.1, dispersion=.05, size=8)
scene.render("render.png", eevee=False,
             size=(800, 800), contrast="Very High Contrast", samples=64)
