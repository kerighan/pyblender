from pyblender.mesh import Box
from pyblender.material import Material

DURATION = 5
N_FRAMES = DURATION * 30

def create_material():
    mat = Material()
    occlusion = mat.create_ambient_occlusion(samples=32)
    cr_1 = mat.create_color_ramp(
        colors=["#000000", "#FFFFFF"])
    mix = mat.create_mix_rgb("MULTIPLY")
    cr_2 = mat.create_color_ramp(
        positions=[0, .85],
        colors=["#00605D", "#D8654E"],
        interpolation="CONSTANT")
    
    occlusion["Color"].to(cr_1["Fac"])
    occlusion["Color"].to(cr_2["Fac"])
    cr_1["Color"].to(mix[2])
    cr_2["Color"].to(mix[1])
    mix["Color"].to(mat.bsdf["Base Color"])
    return mat


def iteration(geometry, position, exponent, C):
    separate_xyz = geometry.create_separate_xyz()
    WR = geometry.create_vector_math("LENGTH")
    WR_cart = geometry.create_operation("POWER")
    WO = geometry.create_operation("ARCCOSINE")
    WO_divide = geometry.create_operation("DIVIDE", value=1)
    WO_cart = geometry.create_operation("MULTIPLY")
    WO_sin = geometry.create_operation("SINE")
    WO_cos = geometry.create_operation("COSINE")
    WI = geometry.create_operation("ARCTAN2")
    # WI_divide = geometry.create_operation("DIVIDE", value=1)
    WI_cart = geometry.create_operation("MULTIPLY")
    WI_sin = geometry.create_operation("SINE")
    WI_cos = geometry.create_operation("COSINE")
    add_C = geometry.create_vector_math("ADD")

    position[0].to(separate_xyz["Vector"])
    position[0].to(WR["Vector"])
    WR["Value"].to(WR_cart[0])
    exponent["Value"].to(WR_cart[1])

    separate_xyz["Y"].to(WO_divide[0])

    WR["Value"].to(WO_divide[1])
    WO_divide["Value"].to(WO[0])
    WO[0].to(WO_cart[0])
    exponent["Value"].to(WO_cart[1])

    separate_xyz["X"].to(WI[0])
    separate_xyz["Z"].to(WI[1])
    WI[0].to(WI_cart[0])
    exponent["Value"].to(WI_cart[1])

    WO_cart[0].to(WO_sin[0])
    WO_cart[0].to(WO_cos[0])
    WI_cart[0].to(WI_sin[0])
    WI_cart[0].to(WI_cos[0])

    combine_x = geometry.create_operation("MULTIPLY")
    WO_sin[0].to(combine_x[0])
    WI_sin[0].to(combine_x[1])
    x = geometry.create_operation("MULTIPLY")
    combine_x[0].to(x[0])
    WR_cart[0].to(x[1])

    y = geometry.create_operation("MULTIPLY")
    WO_cos[0].to(y[0])
    WR_cart[0].to(y[1])

    combine_z = geometry.create_operation("MULTIPLY")
    WO_sin[0].to(combine_z[0])
    WI_cos[0].to(combine_z[1])
    z = geometry.create_operation("MULTIPLY")
    combine_z[0].to(z[0])
    WR_cart[0].to(z[1])

    vector = geometry.create_combine_xyz()
    x[0].to(vector["X"])
    y[0].to(vector["Y"])
    z[0].to(vector["Z"])
    vector["Vector"].to(add_C[0])
    C[0].to(add_C[1])
    return add_C


def get_fractal(resolution=128):
    fractal = Box()
    fractal.rotate(0, 0, -90)
    mat = create_material()
    geometry = fractal.modify_geometry()
    volume = geometry.create_volume_cube(resolution=resolution)
    position = geometry.create_position()
    exponent = geometry.create_value(value=8)
    length = geometry.create_vector_math("LENGTH")
    volume_to_mesh = geometry.create_volume_to_mesh(
        resolution_mode="VOXEL_AMOUNT")
    volume_to_mesh["Voxel Amount"] = resolution
    set_material = geometry.create_set_material(mat)
    
    multiply = geometry.create_operation("MULTIPLY", -1)
    add = geometry.create_operation("ADD", 2.5)
    clamp = geometry.create_clamp()
    is_less_than = geometry.create_operation("LESS_THAN", 2)
    
    vector = iteration(geometry, position, exponent, position)
    vector = iteration(geometry, vector, exponent, position)
    vector = iteration(geometry, vector, exponent, position)
    vector = iteration(geometry, vector, exponent, position)

    vector[0].to(length[0])
    
    
    length["Value"].to(multiply[0])
    multiply["Value"].to(add[0])
    add["Value"].to(clamp[0])
    clamp[0].to(volume["Density"])
    # length["Value"].to(is_less_than[0])
    # is_less_than[0].to(volume["Density"])
    
    volume["Volume"].to(volume_to_mesh["Volume"])
    volume_to_mesh["Mesh"].to(set_material[0])
    set_material["Geometry"].to(geometry.out_node[0])
    # volume_to_mesh["Mesh"].to(geometry.out_node[0])
    
    import numpy as np
    
    exponent.animate_value(
        (5.8) + 2.*np.cos(np.linspace(0, 2*np.pi, N_FRAMES+1)))
    return fractal
