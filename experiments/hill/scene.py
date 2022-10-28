
from pyblender.light import Sun
from pyblender import Scene, Camera
from postproduction import add_effects
from meshes import add_bareers, add_bushes, add_arrows, add_car, add_fences, add_panel, add_road, add_sky, add_steet_lamps, add_hill
DURATION = 5*30

Sun(energy=1)
road_radius = 25
road_width = 3.3
road_lines_width = .1
div = 256
cam_offset = 1.8

position = -road_radius - road_width / 2 + .6
add_hill()
# add_car(position)
add_road(div=div,
         road_radius=road_radius,
         road_width=road_width,
         road_lines_width=road_lines_width)
add_sky()
# add_steet_lamps(road_radius + road_width + 1, count=10)
# add_arrows(road_radius + road_width, count=5)
# add_fences(road_radius + road_width, count=3)
# add_panel(road_radius - 1.8, count=1)
add_bareers(road_radius + road_width - .2, count=40)
add_bareers(road_radius - road_width - .05, count=15)

camera = Camera((12, position + cam_offset, 1.9))
camera.look_at((-10, position + 3.3, 1))
scene = Scene(size=(720, 720))
scene.set_freestyle(line_thickness=.5)
add_effects(scene)
scene.set_animation_bounds(1, DURATION)
scene.render("render.png",
             contrast="Very High Contrast",
             view_transform="Standard", frame=110)
# 110, 67