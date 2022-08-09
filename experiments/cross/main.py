import numpy as np
from experiments.materials import create_sky_mat
from pyblender import Camera, Scene
from pyblender.geometry import Geometry
from pyblender.light import PointLight, Sun
from pyblender.material import EmissionMaterial, Material, VolumeMaterial
from pyblender.mesh import Box, Empty, Plane, Text, UVSphere
from pyblender.texture import Noise

# create sky
# sky = UVSphere(radius=200, location=(0, 0, 100), material=create_sky_mat())
# sky.shade_smooth()

A = 4
PointLight((-A, -A, 0), energy=500, color="#F916D7")
PointLight((-A, A, 0), energy=500, color="#009CF8")

# text_material = EmissionMaterial("#F916D7")
# R = Text("r", size=.2, extrude=.03,
#          material=text_material,
#          font="/home/maixent/fonts/Poppins-Bold.ttf")
# R.translate(-2*A, -2*A, 0)
# E = Text("e", size=.2, extrude=.03,
#          material=text_material,
#          font="/home/maixent/fonts/Poppins-Bold.ttf")
# E.rotate(0, 0, 90).rotate(0, 85, 0).translate(1.1, .3, .05)
# B = Text("b", size=.2, extrude=.03,
#          material=text_material,
#          font="/home/maixent/fonts/Poppins-Bold.ttf")
# B.rotate(0, 0, 90).rotate(0, 85, 0).translate(.8, .5, .05)
# O = Text("o", size=.2, extrude=.03,
#          material=text_material,
#          font="/home/maixent/fonts/Poppins-Bold.ttf")
# O.rotate(0, 0, 90).rotate(0, 85, 0).translate(.25, .75, .03)
# O = Text("o", size=.2, extrude=.03,
#          material=text_material,
#          font="/home/maixent/fonts/Poppins-Bold.ttf")
# O.rotate(0, 0, 90).rotate(0, 85, 0).translate(.6, .92, .06)
# T = Text("t", size=.2, extrude=.03,
#          material=text_material,
#          font="/home/maixent/fonts/Poppins-Bold.ttf")
# T.rotate(0, 0, 90).rotate(0, 85, 0).translate(.65, 1.1, .1)


# PointLight((0, 0, 0), energy=6000, color="#009CF8")
DURATION = 8

material = Material(metallic=1)
cube = Box(material=material)
cube.set_visible(False)

N = 60
source = Plane()
# source.subdivide(10)
nodes = source.modify_geometry()
mesh_node = nodes.create_cube(size=(2.7, 2.7, 2.7), vertices=(N, N, N))

# mesh_node = nodes.create_icosphere()

texture = Noise(type="CLOUDS")
source.modify_displace(texture, strength=60)

geo = source.modify_geometry()
inst = geo.create_instance_on_points()
object_info = geo.create_object_info(cube)
geo.in_node["Geometry"].to(inst["Points"])
inst[0].to(geo.out_node["Geometry"])
object_info["Geometry"].to(inst["Instance"])
rand = geo.create_random_value()
rand2 = geo.create_random_value("FLOAT_VECTOR")
rand_rotation = geo.create_random_value("FLOAT_VECTOR")
add_vector = geo.create_vector_math("ADD")
scale_vector = geo.create_vector_math("SCALE")
value = geo.create_value()
rand[3] = .3
rand2[3] = 6
rand2["Value"].to(add_vector["Vector"])
rand_rotation["Value"].to(scale_vector["Vector"])
scale_vector["Vector"].to(add_vector[1])
rand[1].to(inst["Scale"])
add_vector[0].to(inst["Rotation"])

scale_vector.animate("Scale", np.linspace(1, 8, 24*DURATION),
                     range(1, 24*DURATION))

intensity = (np.cos(np.pi * np.arange(24*DURATION) / 24)/2 + .5) * 10 + 10
intensity2 = (np.cos(np.pi * np.arange(24*DURATION) /
              24 + np.pi)/2 + .5) * 10 + 10

branch_mat = EmissionMaterial(emission_strength=10, color="#1E88D6")
branch_mat_red = EmissionMaterial(emission_strength=10, color="#F916D7")
bsdf_1 = branch_mat.bsdf
bsdf_1.animate("Strength", intensity, range(1, 24*DURATION))
bsdf_2 = branch_mat_red.bsdf
bsdf_2.animate("Strength", intensity2, range(1, 24*DURATION))

# box = Box(size=100, material=vol_mat)
w = .1
branch = Box(scale=(w, w, 100), material=branch_mat)
branch2 = Box(scale=(100, w, w), material=branch_mat)
branch3 = Box(scale=(w, 100, w), material=branch_mat_red)

dist = 50
camera = Camera(location=(dist, dist, 25), lens=100)
camera.look_at((0, 0, 0))

scene = Scene(camera)
scene.add_glare()
scene.set_animation_bounds(1, 24*DURATION)
scene.render("render.mp4",
             eevee=False,
             size=(1920, 1080),
             contrast="Very High Contrast",
             samples=128)
