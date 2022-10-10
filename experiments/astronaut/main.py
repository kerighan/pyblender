from pyblender import Camera, Scene
from pyblender.light import PointLight, Sun
from pyblender.material import Material
from pyblender.mesh import Model

Sun(energy=100)
PointLight((2, 0, 1), energy=200)

# head material
head_mat = Material(
    texture="textures/T_M_MED_Weird_Objects_Creature_HEAD_D.tga.png")

# body material
body_mat = Material(
    texture="textures/T_M_MED_Weird_Objects_Creature_BODY_D.tga.png")

mdl = Model("Ymca Dance.fbx")
mdl.rotate(0, 0, 90)
mdl.translate(0, 0, -.8)
head = mdl.parts[1]
body = mdl.parts[2]
head.add_material(head_mat)
body.add_material(body_mat)

camera = Camera((3, 0, 0))
camera.look_at((0, 0, 0))

scene = Scene(cycles=True)
scene.set_animation_bounds()
compositor = scene.create_compositor()
glare = compositor.create_glare(size=15)
beams = compositor.create_sun_beams(size=.5)
mix_rgb = compositor.create_mix_rgb(blend_type="SCREEN")
compositor.input[0].to(glare[0])
glare[0].to(beams[0])
glare[0].to(mix_rgb[1])
beams[0].to(mix_rgb[2])
mix_rgb[0].to(compositor.output[0])

scene.render("render.png")
