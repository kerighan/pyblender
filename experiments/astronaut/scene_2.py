from pyblender import Camera, Scene
from pyblender.animation import shake
from pyblender.light import PointLight, Sun
from pyblender.material import Material
from pyblender.mesh import Model, UVSphere

DURATION = 30*4

# -----------------------------------------------------------------------------
# LIGHTING
# -----------------------------------------------------------------------------
sun = Sun(energy=10)
PointLight((2, 1.5, 1.5), energy=7000)
PointLight((-2, 1.5, 1.5), energy=50)

# -----------------------------------------------------------------------------
# DEMOGORGON
# -----------------------------------------------------------------------------
mdl = Model("model/Rumba Dancing.fbx")
mdl.repeat_animation(10)
mdl.rotate(0, 90, 0)
mdl.translate(.998, 0, 0)
mdl.scale(.05)
# add materials to the different parts of the mesh
head_mat = Material(
    texture="textures/head.png",
    normal="textures/NormalMap_head.png",
    displacement="textures/DisplacementMap_head.png",
    displacement_scale=.1, displace=True, bump=True, roughness=.5)
mdl.parts[1].add_material(head_mat)
body_mat = Material(
    texture="textures/body.png",
    normal="textures/NormalMap_body.png",
    displacement="textures/DisplacementMap_body.png",
    displacement_scale=.1, displace=True, bump=True, roughness=.5)
mdl.parts[2].add_material(body_mat)

# -----------------------------------------------------------------------------
# MOON
# -----------------------------------------------------------------------------
moon_texture = Material()
texture = moon_texture.create_texture("textures/lroc_color_poles_16k.tif")
displacement = moon_texture.create_displacement(scale=.01)
# shader graph
texture["Color"].to(moon_texture.bsdf["Base Color"])
texture["Color"].to(displacement["Height"])
displacement[0].to(moon_texture.material_output["Displacement"])
# create moon sphere
moon = UVSphere(material=moon_texture, radius=1, div=100)
moon.shade_smooth()

# -----------------------------------------------------------------------------
# CAMERA
# -----------------------------------------------------------------------------
camera = Camera(lens=50)
camera.rotate(94, 90, 0)
camera.translate(1.025, -.25, 0)
camera.animate_location(*shake([1, 2*DURATION],
                               (1.025, -.25, 0),
                               freq=.2, intensity=.00013))

# -----------------------------------------------------------------------------
# SCENE
# -----------------------------------------------------------------------------
scene = Scene(cycles=True, samples=512, size=(720, 720))
scene.set_animation_bounds(DURATION + 1, 2*DURATION)

# -----------------------------------------------------------------------------
# POST PROCESSING
# -----------------------------------------------------------------------------
compositor = scene.create_compositor()
dirt = compositor.create_image("dirt.png")
glare = compositor.create_glare(size=9, mix=1)
mix = compositor.create_mix_rgb(fac=1, blend_type="MULTIPLY")
mix_2 = compositor.create_mix_rgb(fac=.85, blend_type="MIX")
distort = compositor.create_lens_distortion(distortion=-.06, dispersion=.06)
cc = compositor.create_color_correction(contrast=1.03,
                                        saturation=.9)
# compositing graph
compositor.input["Image"].to(glare["Image"])
glare["Image"].to(mix[1])
dirt["Alpha"].to(mix[2])
compositor.input["Image"].to(mix_2[1])
mix["Image"].to(mix_2[2])
mix_2["Image"].to(distort["Image"])
distort["Image"].to(cc["Image"])
cc["Image"].to(compositor.output["Image"])

# render scene
scene.render("scene_2.mp4", frame_rate=30)
