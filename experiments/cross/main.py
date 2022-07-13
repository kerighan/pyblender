from pyblender import Camera, Scene
from pyblender.geometry import Geometry
from pyblender.light import PointLight, Sun
from pyblender.material import EmissionMaterial, Material, VolumeMaterial
from pyblender.mesh import Box, Empty, Plane
from pyblender.texture import Noise

A = 4
PointLight((-A, -A, 0), energy=500, color="#FF1E04")
PointLight((-A, A, 0), energy=500, color="#009CF8")
# PointLight((0, 0, 0), energy=6000, color="#009CF8")

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
rand2 = geo.create_random_value()
rand[3] = .3
rand2[3] = 6
rand[1].to(inst["Scale"])
rand2[1].to(inst["Rotation"])

# vol_mat = VolumeMaterial(density=.9, color="#000000")
branch_mat = EmissionMaterial(emission_strength=10, color="#1E88D6")
branch_mat_red = EmissionMaterial(emission_strength=10, color="#FF1E04")
# box = Box(size=100, material=vol_mat)
w = .1
branch = Box(scale=(w, w, 100), material=branch_mat)
branch2 = Box(scale=(100, w, w), material=branch_mat)
branch3 = Box(scale=(w, 100, w), material=branch_mat_red)

dist = 50
camera = Camera(location=(dist, dist, 25), lens=100)
# camera.look_at((0, 0, 0))
empty = Empty((0, 0, 0))
camera.look_at(empty)
empty.animate_rotation([(-11, 90, 32), (.5, 0, 0)], [0, 100])
# empty.animate_location([(10, 10, 10), (.5, 0, 0)], [0, 100])

scene = Scene(camera)
scene.add_glare()
scene.render("render.png", eevee=False,
             size=(1920, 1080), contrast="Very High Contrast", samples=4096)
