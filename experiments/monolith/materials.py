from pyblender.material import Material


def create_sky_mat():
    sky_mat = Material(cast_shadows=False)
    noise = sky_mat.create_noise_texture(scale=1000, detail=6)
    color_ramp = sky_mat.create_color_ramp(positions=[.70, .71])
    color_ramp2 = sky_mat.create_color_ramp(positions=[.5, .9])
    clouds = sky_mat.create_noise_texture(scale=8, detail=12,
                                          noise_dimensions="4D")
    mix_rgb = sky_mat.create_mix_rgb()
    mult = sky_mat.create_operation(value=.015)
    mult2 = sky_mat.create_operation(value=4)

    clouds.animate("W", [0, .1], [0, 60*5])

    noise["Color"].to(color_ramp["Fac"])
    color_ramp["Color"].to(mix_rgb[1])

    clouds["Color"].to(color_ramp2["Fac"])
    color_ramp2["Color"].to(mult[0])
    mult[0].to(mix_rgb[0])
    mix_rgb[0].to(sky_mat.bsdf["Base Color"])
    mix_rgb[0].to(mult2[0])
    mult2[0].to(sky_mat.bsdf["Emission"])
    return sky_mat


def create_terrain_mat():
    plane_mat = Material(displace=True, specular=1, roughness=.25)
    disp = plane_mat.create_displacement(scale=3, midlevel=0)
    noise = plane_mat.create_noise_texture(scale=3, detail=16)
    noise_2 = plane_mat.create_noise_texture(scale=100, detail=16)
    cr = plane_mat.create_color_ramp(positions=[.37, 1],
                                     interpolation="EASE")
    cr2 = plane_mat.create_color_ramp(positions=[0, .1])
    add = plane_mat.create_operation("ADD")
    mult = plane_mat.create_operation("MULTIPLY", 0.5)

    noise["Fac"].to(cr["Fac"])
    cr["Color"].to(disp["Height"])
    disp[0].to(plane_mat.material_output["Displacement"])

    noise_2["Fac"].to(plane_mat.bsdf["Base Color"])
    noise_2["Fac"].to(plane_mat.bsdf["Roughness"])
    noise_2["Fac"].to(plane_mat.bsdf["Metallic"])
    noise_2["Fac"].to(mult[0])
    mult[0].to(plane_mat.bsdf["Normal"])
    return plane_mat
