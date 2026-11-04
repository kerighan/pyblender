"""Rigid bodies, tweens and groups: cubes drop on a floor, bounce, then fly away in a wave."""

import pyblender as pb

floor = pb.Plane(size=30, material=pb.Material(color="#E5E1DA", roughness=0.8, metallic=0))
floor.rigid_body("PASSIVE", shape="BOX", bounciness=0.3)

cubes = pb.Group(
    pb.Cube(location=(x, y, 4 + (x + y) % 3), rotation=(x * 20, y * 15, 0), size=0.8,
            material=pb.Material(color=(0.2 + 0.1 * x, 0.3, 0.9 - 0.1 * y), roughness=0.3))
    for x in range(-2, 3) for y in range(-2, 3)
)
for cube in cubes:
    cube.rigid_body(mass=1, bounciness=0.5, friction=0.6, shape="BOX")

pb.Sun(energy=4, angle=3, target=(0, 0, 0), location=(6, -8, 12))
pb.AreaLight((-6, -6, 6), energy=800, size=(4, 4), target=(0, 0, 0))
pb.Camera((11, -11, 7), target=(0, 0, 1), lens=45, focus=True, aperture_fstop=4)

pb.scene().set_background("#B9C6D2", strength=0.6)
pb.render("renders/falling_cubes.mp4", frames=120, bake=True, size=(1280, 720), samples=32)
