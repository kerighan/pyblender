

def diffuse_to_rgb(
    mesh,
    index=0,
    colors=["#1A1A1A", "#555555", "#A0A0A0"],
    positions=[0, 0.006, 0.045]
):
    mat = mesh.get_material(index)
    diffuse = mat.create_diffuse_bsdf()
    shader_to_rgb = mat.create_shader_to_rgb()
    color_ramp = mat.create_color_ramp(colors=colors,
                                       positions=positions,
                                       interpolation="CONSTANT")

    diffuse["Color"] = "#FFFFFF"
    diffuse[0].to(shader_to_rgb[0])
    shader_to_rgb[0].to(color_ramp["Fac"])
    color_ramp[0].to(mat.material_output["Surface"])
    
def emission_shader(mesh, index=0, color="#FFBA00", strength=4):
    mat = mesh.get_material(index)
    emission = mat.create_emission(color=color, strength=strength)
    emission[0].to(mat.material_output["Surface"])


def gradient_shader(mat, index=0, colors=["#111111", "#4F7BFF"], offset=.62):
    # mat = mesh.get_material(index)
    cam_data = mat.create_camera_data()
    logarithm = mat.create_operation(operation="LOGARITHM", value=15)
    subtract = mat.create_operation(operation="SUBTRACT", value=offset)
    color_ramp = mat.create_color_ramp(positions=[0, .95], interpolation="EASE")
    mix_shader = mat.create_mix_shader()
    rgb_1 = mat.create_rgb(colors[0])
    rgb_2 = mat.create_rgb(colors[1])
    
    cam_data["View Z Depth"].to(logarithm[0])
    logarithm[0].to(subtract[0])
    subtract[0].to(color_ramp["Fac"])
    color_ramp["Color"].to(mix_shader["Fac"])
    
    rgb_1[0].to(mix_shader[1])
    rgb_2[0].to(mix_shader[2])
    mix_shader[0].to(mat.material_output["Surface"])


def soft_emission(mat, color):
    rgb = mat.create_rgb(color=color)
    rgb["Color"].to(mat.bsdf["Base Color"])
    separate = mat.create_separate_hsv()
    combine = mat.create_combine_hsv()
    operation = mat.create_operation(value=.3)
    
    mat.bsdf["Emission Strength"] = 1.
    # mat.bsdf["Emission"] = "#FFFFFF"
    rgb["Color"].to(separate["Color"])
    separate["H"].to(combine["H"])
    separate["S"].to(combine["S"])
    separate["V"].to(operation[0])
    operation[0].to(combine["V"])
    combine["Color"].to(mat.bsdf["Emission"])    
