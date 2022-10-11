from pyblender import Camera, Scene
from pyblender.animation import shake
from pyblender.light import PointLight
from pyblender.material import Material
from pyblender.mesh import Model, UVSphere

DURATION = 30*4
PointLight((2, 1.5, 1.5), energy=8000)

# head material
head_mat = Material(
    texture="textures/head.png",
    normal="textures/NormalMap_head.png",
    displacement="textures/DisplacementMap_head.png",
    displacement_scale=.1,
    displace=True, bump=True,
    roughness=.5)
# body material
body_mat = Material(
    texture="textures/body.png",
    normal="textures/NormalMap_body.png",
    displacement="textures/DisplacementMap_body.png",
    displacement_scale=.1,
    displace=True, bump=True,
    roughness=.5)
mdl = Model("model/Rumba Dancing.fbx")
mdl.repeat_animation(10)
mdl.rotate(0, 90, 0)
mdl.translate(.998, 0, 0)
mdl.scale(.05)
mdl.parts[1].add_material(head_mat)
mdl.parts[2].add_material(body_mat)

# -------------------------
# MOON
# -------------------------
moon_texture = Material()
texture = moon_texture.create_texture("textures/lroc_color_poles_16k.tif")
displacement = moon_texture.create_displacement(scale=.01)
texture["Color"].to(moon_texture.bsdf["Base Color"])
texture["Color"].to(displacement["Height"])
displacement[0].to(moon_texture.material_output["Displacement"])
moon = UVSphere(material=moon_texture, radius=1, div=64)
moon.shade_smooth()

camera = Camera((5, 0, 0), lens=10)
camera.look_at((0, 0, 0))
camera.animate_lens([15, 800], [1, DURATION])
camera.animate_location(*shake([1, DURATION], (5, 0, 0),
                               freq=.2, intensity=.00013))

scene = Scene(cycles=True, samples=512, size=(720, 720))
scene.set_animation_bounds(1, DURATION)

compositor = scene.create_compositor()
dirt = compositor.create_image("dirt.png")
glare = compositor.create_glare(size=9, mix=1)
mix = compositor.create_mix_rgb(fac=1, blend_type="MULTIPLY")
mix_2 = compositor.create_mix_rgb(fac=.85, blend_type="MIX")
distort = compositor.create_lens_distortion(distortion=-.05, dispersion=.05)
cc = compositor.create_color_correction(contrast=1.05,
                                        saturation=.9)
compositor.input["Image"].to(glare["Image"])
glare["Image"].to(mix[1])
dirt["Alpha"].to(mix[2])
compositor.input["Image"].to(mix_2[1])
mix["Image"].to(mix_2[2])
mix_2["Image"].to(distort["Image"])
distort["Image"].to(cc["Image"])
cc["Image"].to(compositor.output["Image"])


scene.render("scene_1.mp4", frame_rate=30, frame=80)
