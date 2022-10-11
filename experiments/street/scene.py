from pyblender import Box, Camera, Material, Scene, Sphere
from pyblender.light import PointLight

# Sun()
PointLight((1, 2, 2), energy=800, color="#88CED3")


material = Material(roughness=.8)
texture = material.create_texture("sprites/FLOOR_3A.png",
                                  projection="BOX")
normal = material.create_texture("sprites/FLOOR_3A_NORMAL2.png",
                                 projection="BOX",
                                 color_space="Non-Color")
texcoord, mapping = material.create_texture_coordinate()
normal_map = material.create_normal_map(strength=2)
bump = material.create_bump(strength=2)
texcoord["Object"].to(mapping["Vector"])
mapping[0].to(texture["Vector"])
mapping[0].to(normal["Vector"])
texture[0].to(material.bsdf["Base Color"])
texture[0].to(bump["Height"])
normal[0].to(normal_map["Color"])
normal_map["Normal"].to(bump["Normal"])
bump["Normal"].to(material.bsdf["Normal"])

Sphere(location=(0, 0, .5),
       material=Material(emission_strength=200, emission_color="#EBCE8F"),
       radius=.2)

Box(material=material, scale=(5, 5, .1))

camera = Camera((3, 0, 2))
camera.look_at((0, 0, 0))

scene = Scene(cycles=True, samples=64, size=(720, 720))
scene.render("render.png")
