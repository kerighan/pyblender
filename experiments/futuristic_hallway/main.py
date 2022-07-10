from pyblender import Scene, Camera
from pyblender.material import Material, EmissionMaterial
from pyblender.mesh import Box, Empty, Plane
from pyblender.light import PointLight, Sun
from pyblender.texture import Noise

noise = Noise(
    noise_scale=.2,
    noise_basis="CELL_NOISE",
    noise_distortion="CELL_NOISE"
)


material = Material(metallic=.1, color="#232323")

mix = material.create_mix_shader()
emission = material.create_emission(color="#0032FE")
noise_tex = material.create_noise_texture(scale=5)
mapping = material.create_mapping()
color_ramp = material.create_color_ramp(
    colors=["#000000", "#FFFFFF"], positions=[.64, 1])
geometry = material.create_geometry()

mix["Shader"].to(material.material_output["Surface"])
geometry["True Normal"].to(mapping["Vector"])
mapping["Vector"].to(noise_tex["Vector"])
noise_tex["Color"].to(color_ramp["Fac"])
color_ramp["Color"].to(mix["Fac"])
material.bsdf["BSDF"].to(mix[1])
emission["Emission"].to(mix[2])
noise_tex["W"] = .01

DEPTH = 16
PointLight((0, 0, 0), energy=20, color="#0032FE")
PointLight((-DEPTH, 0, 0), energy=300, color="#DE213D", attenuation=.2)
PointLight((-2*DEPTH, 0, 0), energy=20, color="#0032FE")

empty = Empty((-DEPTH, 0, 0))
box = Box(material=material, scale=(DEPTH*2, 2, 1))
box.remove_face("front")
box.remove_face("back")
box.subdivide(50)
box.modify_subdivide()
box.modify_displace(noise, strength=-.05)
box.modify_mirror(axis=(True, False, False), object=empty)

camera = Camera(location=(0, 0, 0), lens=30)
camera.look_at((-2, 0, .1))
scene = Scene(camera)
# scene.set_animation_bounds(0, 20)
scene.add_bloom(.25, radius=5, threshold=.8)
scene.render("render.png", size=(1920, 1080), use_ssr=True, eevee=False, samples=16)
