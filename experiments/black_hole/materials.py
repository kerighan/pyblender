from pyblender.material import Material, RefractionBSDF

def create_sky_mat():
    sky_mat = Material(cast_shadows=False)
    noise = sky_mat.create_noise_texture(scale=1000, detail=6)
    color_ramp = sky_mat.create_color_ramp(positions=[.69, .70])
    color_ramp2 = sky_mat.create_color_ramp(positions=[.5, .9])
    clouds = sky_mat.create_noise_texture(scale=2, detail=12,
                                          noise_dimensions="3D")
    mix_rgb = sky_mat.create_mix_rgb()
    mult = sky_mat.create_operation(value=.25)

    noise["Color"].to(color_ramp["Fac"])
    color_ramp["Color"].to(sky_mat.bsdf["Emission"])
    color_ramp["Color"].to(mix_rgb[1])

    clouds["Color"].to(color_ramp2["Fac"])
    color_ramp2["Color"].to(mult[0])
    mult[0].to(mix_rgb[0])
    mix_rgb[0].to(sky_mat.bsdf["Base Color"])
    return sky_mat


def create_black_hole_mat():    
    mat = RefractionBSDF(color="#FFFFFF", roughness=0)
    layer_weight = mat.create_layer_weight(blend=.96)
    mix_shader = mat.create_mix_shader()
    cr = mat.create_color_ramp(positions=[0.5, .7])
    op = mat.create_operation("POWER", -1)
    
    layer_weight["Facing"].to(op[0])
    op[0].to(mat.bsdf["IOR"])
    cr["Color"].to(mix_shader["Fac"])
    mat.bsdf[0].to(mix_shader[2])
    layer_weight["Facing"].to(cr["Fac"])
    mix_shader[0].to(mat.material_output["Surface"])
    return mat
