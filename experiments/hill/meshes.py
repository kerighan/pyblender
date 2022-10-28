from math import radians
from pyblender.curve import Bezier
from pyblender.mesh import Box, Model, Plane, Circle
from materials import diffuse_to_rgb, emission_shader, gradient_shader, soft_emission
from pyblender.material import Material
from pyblender.utils import to_radians
import numpy as np

DURATION = 30*5

def add_car(road_radius):
    colors = ["#1A1A1A", "#555555", "#FBF2E9"]
    car = Model("../../../veryveig/car.fbx")
    car.rotate(-90, 0, -2)
    car.translate(0, road_radius, .7)
    diffuse_to_rgb(car, index=0, colors=colors)
    diffuse_to_rgb(car, index=1, positions=[0, 0.003, 0.82], colors=colors)
    diffuse_to_rgb(car, index=2, colors=colors)
    diffuse_to_rgb(car, index=3, positions=[0, 0.003, 0.1], colors=colors)
    emission_shader(car, index=8, color="#BB7E0F")
    mat = car.get_material(4)
    bsdf = mat.get_node("Principled BSDF")
    bsdf["Rougness"] = .19
    bsdf["Transmission"] = 1
    bsdf["Base Color"] = "#28315E"
    
    tires = car.get_material("Material-reflector.003")
    texture = tires.create_texture("../../../veryveig/textures/rimstock_18.png")
    texture[0].to(tires.bsdf["Base Color"]) 


def add_road(div=32, road_radius=10, road_width=10, road_lines_width=.15):
    road_circle = Circle(radius=road_radius, div=div)
    road_circle.animate_rotation_z(np.linspace(0, 360, DURATION))
    road = Box(material=Material())
    
    mat = Material(emission_strength=1)
    gradient_shader(mat, colors=["#101010", "#00605D"])

    # ROAD
    geometry = road.modify_geometry()
    join_geometry = geometry.create_join_geometry()
    mesh_to_curve = geometry.create_mesh_to_curve()
    curve_to_mesh_1 = geometry.create_curve_to_mesh()
    object_info = geometry.create_object_info(road_circle, "RELATIVE")
    curve_line = geometry.create_curve_line()
    set_material_1 = geometry.create_set_material(mat)
    
    curve_line["Start"] = (-road_width, 0, 0)
    curve_line["End"] = (road_width, 0, 0)

    object_info["Geometry"].to(mesh_to_curve["Mesh"])
    mesh_to_curve["Curve"].to(curve_to_mesh_1["Curve"])    
    curve_line["Curve"].to(curve_to_mesh_1["Profile Curve"])
    curve_to_mesh_1["Mesh"].to(set_material_1["Geometry"])
    
    # ROAD LINES
    curve_line = geometry.create_curve_line()
    curve_to_mesh_2 = geometry.create_curve_to_mesh()
    transform = geometry.create_transform()
    set_material_2 = geometry.create_set_material(Material(emission_strength=1))
    transform["Translation"] = (0, 0, .01)
    curve_line["Start"] = (-road_lines_width, 0, 0)
    curve_line["End"] = (road_lines_width, 0, 0)
    mesh_to_curve["Curve"].to(transform["Geometry"])
    transform[0].to(curve_to_mesh_2["Curve"])
    curve_line["Curve"].to(curve_to_mesh_2["Profile Curve"])
    
    # OUTER ROAD LINES
    road_join_geometry = geometry.create_join_geometry()
    curve_to_mesh_3 = geometry.create_curve_to_mesh()
    set_position = geometry.create_set_position()
    normal = geometry.create_normal()
    scale = geometry.create_operation("SCALE", value=.85*road_width)
    normal[0].to(scale[0])
    scale[0].to(set_position["Offset"])
    transform[0].to(set_position["Geometry"])
    set_position[0].to(curve_to_mesh_3["Curve"])
    curve_line["Curve"].to(curve_to_mesh_3["Profile Curve"])
    
    curve_to_mesh_4 = geometry.create_curve_to_mesh()
    set_position = geometry.create_set_position()
    scale = geometry.create_operation("SCALE", value=-.85*road_width)
    normal[0].to(scale[0])
    scale[0].to(set_position["Offset"])
    transform[0].to(set_position["Geometry"])
    set_position[0].to(curve_to_mesh_4["Curve"])
    curve_line["Curve"].to(curve_to_mesh_4["Profile Curve"])
    
    # break road lines
    curve_to_points = geometry.create_curve_to_points(count=21)
    instance_on_points = geometry.create_instance_on_points()
    cube = geometry.create_cube(size=(.5, 1, 3.5))
    mesh_boolean = geometry.create_mesh_boolean()
    mesh_to_curve["Curve"].to(curve_to_points["Curve"])
    curve_to_points["Points"].to(instance_on_points["Points"])
    curve_to_points["Rotation"].to(instance_on_points["Rotation"])
    cube["Mesh"].to(instance_on_points["Instance"])
    instance_on_points[0].to(mesh_boolean[1])
    curve_to_mesh_2["Mesh"].to(mesh_boolean[0])

    mesh_boolean[0].to(road_join_geometry[0])
    curve_to_mesh_3[0].to(road_join_geometry[0])
    curve_to_mesh_4[0].to(road_join_geometry[0])
    road_join_geometry["Geometry"].to(set_material_2["Geometry"])
    
    # barreers
    # bezier = Bezier([(0, 0, 0), (1, 1, 0), (2, 0, 0), (3, 1, 0)])
    # curve_to_mesh_5 = geometry.create_curve_to_mesh()
    # object_info = geometry.create_object_info(bezier, "RELATIVE")
    # curve_line = geometry.create_curve_line()
    # object_info["Geometry"].to(curve_to_mesh_5["Profile Curve"])

    # join all geometries
    set_material_1["Geometry"].to(join_geometry[0])
    set_material_2["Geometry"].to(join_geometry[0])
    join_geometry[0].to(geometry.out_node[0])


def add_bareers(road_radius, div=32, count=30):
    road_circle = Circle(radius=road_radius, div=div)
    road_circle.translate(0, 0, .65)
    road_circle.animate_rotation_z(np.linspace(0, 360, DURATION))
    road = Box(material=Material())

    # ROAD
    geometry = road.modify_geometry()
    mesh_to_curve = geometry.create_mesh_to_curve()
    object_info = geometry.create_object_info(road_circle, "RELATIVE")
    object_info["Geometry"].to(mesh_to_curve["Mesh"])

    plot = Model("../../../veryveig/plot.fbx")
    for name in plot.get_material_names():
        if "Sign-Yellow" in name:
            soft_emission(plot.get_material(name), color="#BB7E0F")
        if "SIGN-white" in name:
            soft_emission(plot.get_material(name), color="#FFFFFF")
        
    # Sign-Yellow
    
    curve_to_points = geometry.create_curve_to_points(count=count)
    instance_on_points = geometry.create_instance_on_points()
    object_info = geometry.create_object_info(plot, "ORIGINAL")
    
    mesh_to_curve["Curve"].to(curve_to_points["Curve"])
    curve_to_points["Points"].to(instance_on_points["Points"])
    object_info["Geometry"].to(instance_on_points["Instance"])
    instance_on_points[0].to(geometry.out_node[0])


def add_steet_lamps(road_radius, div=32, count=30):
    road_circle = Circle(radius=road_radius, div=div)
    road_circle.translate(0, 0, 2)
    road_circle.animate_rotation_z(np.linspace(0, 360, DURATION))
    road = Box(material=Material())

    # ROAD
    geometry = road.modify_geometry()
    mesh_to_curve = geometry.create_mesh_to_curve()
    object_info = geometry.create_object_info(road_circle, "RELATIVE")
    object_info["Geometry"].to(mesh_to_curve["Mesh"])

    plot = Model("../../../veryveig/lampadaire.fbx")
    mat = plot.get_material(1)
    mat.bsdf["Emission"] = "#FDBF50"
    mat.bsdf["Emission Strength"] = 20
    
    curve_to_points = geometry.create_curve_to_points(count=count)
    instance_on_points = geometry.create_instance_on_points()
    object_info = geometry.create_object_info(plot, "ORIGINAL")
    separate = geometry.create_separate_xyz()
    combine = geometry.create_combine_xyz()
    op = geometry.create_operation("ADD", radians(180))
    # rotate["Axis"] = (0, 0, 1)
    # rotate["Angle"] = radians(90)

    mesh_to_curve["Curve"].to(curve_to_points["Curve"])
    curve_to_points["Points"].to(instance_on_points["Points"])
    object_info["Geometry"].to(instance_on_points["Instance"])
    curve_to_points["Rotation"].to(separate["Vector"])
    separate[2].to(op[0])
    op[0].to(combine["Z"])
    
    combine["Vector"].to(instance_on_points["Rotation"])
    instance_on_points[0].to(geometry.out_node[0])


def add_arrows(road_radius, div=32, count=30):
    road_circle = Circle(radius=road_radius, div=div)
    road_circle.rotate(0, 0, 5)
    road_circle.translate(0, 0, .8)
    road_circle.animate_rotation_z(np.linspace(0, 360, DURATION))
    road = Box(material=Material())

    # ROAD
    geometry = road.modify_geometry()
    mesh_to_curve = geometry.create_mesh_to_curve()
    object_info = geometry.create_object_info(road_circle, "RELATIVE")
    object_info["Geometry"].to(mesh_to_curve["Mesh"])

    plot = Model("../../../veryveig/arrow.fbx")
    # mat = plot.get_material(1)
    # mat.bsdf["Emission"] = "#FDBF50"
    # mat.bsdf["Emission Strength"] = 20
    for name in plot.get_material_names():
        if "Sign-Poles" in name:
            soft_emission(plot.get_material(name), color="#FFFFFF")
        # else:
        if "Sign-Yellow" in name:  # Lamp-White
            soft_emission(plot.get_material(name), color="#00605D")
        if "Material-Color_007" in name:  # Lamp-White
            soft_emission(plot.get_material(name), color="#FFFFFF")

    # ['Material-紅綠燈暗', 'Sign-Poles Emissive', 'Sign-Yellow', 'Material-Color_007', 'Material-紅燈', 'Material-紅綠燈殼', 'Lamp-White']
    
    print(plot.get_material_names())
    # raise ValueError

    curve_to_points = geometry.create_curve_to_points(count=count)
    instance_on_points = geometry.create_instance_on_points()
    object_info = geometry.create_object_info(plot, "ORIGINAL")
    separate = geometry.create_separate_xyz()
    combine = geometry.create_combine_xyz()
    op = geometry.create_operation("ADD", 0)
    # rotate["Axis"] = (0, 0, 1)
    # rotate["Angle"] = radians(90)

    mesh_to_curve["Curve"].to(curve_to_points["Curve"])
    curve_to_points["Points"].to(instance_on_points["Points"])
    object_info["Geometry"].to(instance_on_points["Instance"])
    curve_to_points["Rotation"].to(separate["Vector"])
    separate[2].to(op[0])
    op[0].to(combine["Z"])

    combine["Vector"].to(instance_on_points["Rotation"])
    instance_on_points[0].to(geometry.out_node[0])


def add_fences(road_radius, div=32, count=30):
    road_circle = Circle(radius=road_radius, div=div)
    road_circle.rotate(0, 0, 13)
    road_circle.translate(0, 0, .45)
    road_circle.animate_rotation_z(np.linspace(0, 360, DURATION))
    road = Box(material=Material())

    # ROAD
    geometry = road.modify_geometry()
    mesh_to_curve = geometry.create_mesh_to_curve()
    object_info = geometry.create_object_info(road_circle, "RELATIVE")
    object_info["Geometry"].to(mesh_to_curve["Mesh"])

    plot = Model("../../../veryveig/fence.fbx")
    for name in plot.get_material_names():
        soft_emission(plot.get_material(name), color="#FFFFFF")

    # raise ValueError

    curve_to_points = geometry.create_curve_to_points(count=count)
    instance_on_points = geometry.create_instance_on_points()
    object_info = geometry.create_object_info(plot, "ORIGINAL")
    separate = geometry.create_separate_xyz()
    combine = geometry.create_combine_xyz()
    op = geometry.create_operation("ADD", radians(90))
    # rotate["Axis"] = (0, 0, 1)
    # rotate["Angle"] = radians(90)

    mesh_to_curve["Curve"].to(curve_to_points["Curve"])
    curve_to_points["Points"].to(instance_on_points["Points"])
    object_info["Geometry"].to(instance_on_points["Instance"])
    curve_to_points["Rotation"].to(separate["Vector"])
    separate[2].to(op[0])
    op[0].to(combine["Z"])

    combine["Vector"].to(instance_on_points["Rotation"])
    instance_on_points[0].to(geometry.out_node[0])


def add_panel(road_radius, div=32, count=30):
    road_circle = Circle(radius=road_radius, div=div)
    road_circle.translate(0, 0, 2)
    road_circle.animate_rotation_z(np.linspace(0, 360, DURATION))
    road = Box(material=Material())

    # ROAD
    geometry = road.modify_geometry()
    mesh_to_curve = geometry.create_mesh_to_curve()
    object_info = geometry.create_object_info(road_circle, "RELATIVE")
    object_info["Geometry"].to(mesh_to_curve["Mesh"])

    plot = Model("../../../veryveig/panel.fbx")
    soft_emission(plot.get_material("SIGN-green"), color="#00605D")
    soft_emission(plot.get_material("Sign-Blue shield"), color="#FBF2E9")
    soft_emission(plot.get_material("SIGN-white"), color="#FBF2E9")
    soft_emission(plot.get_material("Sign Poles"), color="#FFFFFF")
    
    curve_to_points = geometry.create_curve_to_points(count=count)
    instance_on_points = geometry.create_instance_on_points()
    object_info = geometry.create_object_info(plot, "ORIGINAL")
    transform = geometry.create_transform()
    transform["Scale"] = (.7, .7, .7)
    transform["Translation"] = (0, 0, 2.55)
    separate = geometry.create_separate_xyz()
    combine = geometry.create_combine_xyz()
    op = geometry.create_operation("ADD", 0)

    mesh_to_curve["Curve"].to(curve_to_points["Curve"])
    curve_to_points["Points"].to(instance_on_points["Points"])
    object_info["Geometry"].to(transform["Geometry"])
    transform["Geometry"].to(instance_on_points["Instance"])
    curve_to_points["Rotation"].to(separate["Vector"])
    separate[2].to(op[0])
    op[0].to(combine["Z"])
    
    combine["Vector"].to(instance_on_points["Rotation"])
    instance_on_points[0].to(geometry.out_node[0])


def add_plane():
    plane = Plane(size=50, material=Material())
    gradient_shader(plane)
    

def add_sky(src="sky3.jpg"):
    mat = Material(texture=src, emission_strength=1)
    # image = mat.get_node_by_name("Image")
    tex = mat.create_texture(src)
    op = mat.create_operation(value=1.1)
    tex[0].to(mat.bsdf["Emission"])
    tex[0].to(op[0])
    op[0].to(mat.bsdf["Emission Strength"])
    
    plane = Plane(rotation=(90, 0, 90), material=mat, size=50)
    plane.translate(-30, -15, 11)
    plane.scale(1, 1, .6)

    plane2 = Plane(material=Material("#000000"), rotation=(90, 0, 90), size=15)
    plane2.translate(-20, -15, -8)


def add_hill():
    material = Material()
    gradient_shader(material, colors=["#000000", "#161513"])
    
    plane = Plane(size=61, material=material)
    plane.subdivide(20)
    plane.translate(-4,.6, 0)
    plane.animate_rotation_z(np.linspace(0, 360, DURATION))
    plane.modify_displace("hill2.png", strength=26, mid_level=0.09)


def add_bushes(road_radius, div=32, count=30):
    road_circle = Circle(radius=road_radius, div=div)
    road_circle.translate(0, 0, 2)
    road = Box(material=Material())

    # ROAD
    geometry = road.modify_geometry()
    mesh_to_curve = geometry.create_mesh_to_curve()
    object_info = geometry.create_object_info(road_circle, "RELATIVE")
    object_info["Geometry"].to(mesh_to_curve["Mesh"])

    plot = Model("../../../veryveig/bush.fbx")
    curve_to_points = geometry.create_curve_to_points(count=count)
    instance_on_points = geometry.create_instance_on_points()
    object_info = geometry.create_object_info(plot, "ORIGINAL")
    separate = geometry.create_separate_xyz()
    combine = geometry.create_combine_xyz()
    op = geometry.create_operation("ADD", radians(180))
    
    mesh_to_curve["Curve"].to(curve_to_points["Curve"])
    curve_to_points["Points"].to(instance_on_points["Points"])
    object_info["Geometry"].to(instance_on_points["Instance"])
    curve_to_points["Rotation"].to(separate["Vector"])
    separate[2].to(op[0])
    op[0].to(combine["Z"])

    combine["Vector"].to(instance_on_points["Rotation"])
    instance_on_points[0].to(geometry.out_node[0])
