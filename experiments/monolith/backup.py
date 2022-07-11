from pyblender import Scene
from pyblender.camera import Camera
from pyblender.light import PointLight, SpotLight, Sun
from pyblender.material import Material, RefractionBSDF
from pyblender.mesh import Box, Grid, Plane
from pyblender.texture import Noise, Texture

plane_mat = Material(metallic=0, roughness=.9, specular=0)
noise = plane_mat.create_noise_texture(scale=600, detail=6, distortion=.1)
noise_large = plane_mat.create_noise_texture(scale=40, distortion=1)
displacement = plane_mat.create_displacement(scale=10)
addition = plane_mat.create_operation("ADD")
mix_rgb = plane_mat.create_mix_rgb()

noise["Color"].to(addition[0])
noise_large["Color"].to(addition[1])
addition[0].to(displacement["Height"])
displacement[0].to(plane_mat.material_output["Displacement"])
displacement[0].to(plane_mat.bsdf["Normal"])

heightmap = Noise(noise_scale=20,
                  noise_basis="VORONOI_F2",
                  noise_distortion="VORONOI_F2")

plane = Grid(width=500, height=500, material=plane_mat,
             size=200, location=(10, 10, -1))
# plane.subdivide(100)
plane.modify_displace(heightmap, strength=3)
plane.modify_subdivide(render_levels=2)
# plane.modify_smooth()

# light = PointLight(location=(-6, 0, .2), energy=600)
light = SpotLight(location=(-10, 0, 1), energy=10000)
light.look_at((0, 0, 0.1))
PointLight(location=(-13, 4, .2), energy=400, color="#F0462B", attenuation=.1)
PointLight(location=(-13, -4, .2), energy=400, color="#DF8033", attenuation=.1)

# monolith_mat = RefractionBSDF(ior=1.1, roughness=.9)
# monolith = Box(scale=(.3, .9, 2),
#                rotation=(0, 0, 3.141/6),
#                material=monolith_mat)

camera = Camera(location=(4, 0, -.6), lens=30)
camera.look_at((0, 0, .1))
scene = Scene(camera)
scene.render("test.png", eevee=True, size=(1600, 900))
