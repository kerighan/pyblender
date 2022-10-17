from pyblender.material import Material
from pyblender.mesh import Model, Plane
from pyblender.animation import Movement, flicker


SIZE = .1
OFFSET = SIZE * 21 / 2
VELOCITY = 0.015


def create_pacman():
    pacman_z = -.015
    movement = Movement(velocity=VELOCITY, use_rotation=True)
    movement.start_at(4.5*SIZE, -5.5*SIZE, pacman_z)
    movement.move_to(4.5*SIZE, 2.5*SIZE, pacman_z)
    movement.move_to(6.5*SIZE, 2.5*SIZE, pacman_z)
    movement.move_to(6.5*SIZE, .5*SIZE, pacman_z)
    movement.move_to(8.5*SIZE, .5*SIZE, pacman_z)
    movement.move_to(8.5*SIZE, -1.5*SIZE, pacman_z)

    # pacman
    pacman_mat = Material(color="#E2A029", emission_strength=2)
    pacman = Model("models/pacman_opened.obj")
    pacman.set_material(pacman_mat)
    pacman.scale(.06)
    pacman.animate_visibility(flicker(50, 3)[:movement.duration])

    # pacman mouth closed
    pacman_closed = Model("models/pacman_closed.obj")
    pacman_closed.set_material(pacman_mat)
    pacman_closed.scale(.06)
    pacman_closed.animate_visibility(
        flicker(50, 3, False)[:movement.duration])

    # pacman_z = .01
    movement.apply(pacman)
    movement.apply(pacman_closed)

    return movement


def create_ghosts(duration):
    ghost = Model("models/ghost_orange-0-ghost.obj")
    ghost.scale(.07)
    ghost.rotate(0, 0, 90)
    ghost_mat = ghost.get_material()
    texture = ghost_mat.get_node_by_name("Image Texture")
    texture[0].to(ghost_mat.bsdf["Emission"])
    ghost_mat.bsdf["Emission Strength"] = 3

    ghost_z = 0.025
    ghost_mvt = Movement(velocity=VELOCITY)
    ghost_mvt.start_at(2.5*SIZE, -7.5*SIZE, ghost_z)
    ghost_mvt.move_to(2.5*SIZE, -5.5*SIZE, ghost_z)
    ghost_mvt.move_to(4.5*SIZE, -5.5*SIZE, ghost_z)
    ghost_mvt.move_to(4.5*SIZE, 2.5*SIZE, ghost_z)
    ghost_mvt.move_to(6.5*SIZE, 2.5*SIZE, ghost_z)
    ghost_mvt.move_to(6.5*SIZE, .5*SIZE, ghost_z)
    ghost_mvt.move_to(8.5*SIZE, .5*SIZE, ghost_z)
    ghost_mvt.frames = ghost_mvt.frames[:duration]
    ghost_mvt.apply(ghost)

    ghost_2 = Model("models/ghost_2-0-ghost.obj")
    ghost_2.scale(.07)
    ghost_2.rotate(0, 0, 90)
    ghost_2_mat = ghost_2.get_material()
    texture = ghost_2_mat.get_node_by_name("Image Texture")
    texture[0].to(ghost_2_mat.bsdf["Emission"])
    ghost_2_mat.bsdf["Emission Strength"] = 3

    ghost_2_mvt = Movement(velocity=VELOCITY)
    ghost_2_mvt.start_at(-2.5*SIZE, 4.5*SIZE, ghost_z)
    ghost_2_mvt.move_to(4.5*SIZE, 4.5*SIZE, ghost_z)
    ghost_2_mvt.move_to(4.5*SIZE, 2.5*SIZE, ghost_z)
    ghost_2_mvt.move_to(6.5*SIZE, 2.5*SIZE, ghost_z)
    ghost_2_mvt.move_to(6.5*SIZE, .5*SIZE, ghost_z)
    ghost_2_mvt.move_to(8.5*SIZE, .5*SIZE, ghost_z)
    ghost_2_mvt.move_to(8.5*SIZE, -1.5*SIZE, ghost_z)
    ghost_2_mvt.frames = ghost_2_mvt.frames[:duration]
    ghost_2_mvt.apply(ghost_2)

    ghost_3 = Model("models/ghost_red-0-ghost.obj")
    ghost_3.scale(.07)
    ghost_3.rotate(0, 0, 90)
    ghost_3_mat = ghost_3.get_material()
    texture = ghost_3_mat.get_node_by_name("Image Texture")
    texture[0].to(ghost_3_mat.bsdf["Emission"])
    ghost_3_mat.bsdf["Emission Strength"] = 3

    ghost_3_mvt = Movement(velocity=VELOCITY)
    ghost_3_mvt.start_at(-3.5*SIZE, -5.5*SIZE, ghost_z)
    ghost_3_mvt.move_to(4.5*SIZE, -5.5*SIZE, ghost_z)
    ghost_3_mvt.move_to(4.5*SIZE, -3.5*SIZE, ghost_z)
    ghost_3_mvt.move_to(6.5*SIZE, -3.5*SIZE, ghost_z)
    ghost_3_mvt.move_to(6.5*SIZE, -1.5*SIZE, ghost_z)
    ghost_3_mvt.move_to(8.5*SIZE, -1.5*SIZE, ghost_z)
    ghost_3_mvt.apply(ghost_3)


def create_ground():
    ground_mat = Material(color="#161513", roughness=.3)
    noise = ground_mat.create_noise_texture(scale=500, detail=48)
    noise[0].to(ground_mat.bsdf["Roughness"])
    
    ground = Plane(size=OFFSET*5, location=(0, 0, -.012), material=ground_mat)

