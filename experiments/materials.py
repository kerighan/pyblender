from pyblender.material import (EmissionMaterial, Material, RefractionBSDF,
                                VolumeMaterial)


def create_sky_mat(star_intensity=200):
    sky_mat = Material(cast_shadows=False, emission_strength=10)
    bsdf = sky_mat.bsdf

    offset = .015
    cosmos_noise = sky_mat.create_noise_texture(scale=30)
    cosmos_cr = sky_mat.create_color_ramp(
        colors=["#042246", "#0865B3"],
        positions=[0.1, .8], interpolation="EASE")
    stars_noise = sky_mat.create_noise_texture(scale=1100, detail=6)
    stars_cr = sky_mat.create_color_ramp(
        positions=[.694+offset, .697+offset, .70+offset],
        colors=["#000000", "#18469B", "#3CA6D8"])
    stars_light = sky_mat.create_noise_texture(
        scale=25, detail=40, distortion=.3)
    stars_light_cr = sky_mat.create_color_ramp(
        colors=["#021D3B", "#04AADA"],
        positions=[.35, .65], interpolation="EASE")
    stars_light_intensity = sky_mat.create_operation(value=star_intensity)
    stars_shine_mix = sky_mat.create_mix_rgb(
        blend_type="MULTIPLY", fac=0.9)

    stars_noise["Color"].to(stars_cr["Fac"])
    stars_light["Color"].to(stars_light_cr["Fac"])
    # stars_cr["Color"].to(mix_stars_cosmos[2])

    stars2_noise = sky_mat.create_noise_texture(
        scale=900, detail=6)
    stars2_cr = sky_mat.create_color_ramp(
        positions=[.694+offset, .697+offset, .70+offset],
        colors=["#000000", "#E5D48C", "#F2D4AE"])

    stars3_noise = sky_mat.create_noise_texture(
        scale=1000, detail=6, distortion=1)
    stars3_cr = sky_mat.create_color_ramp(
        positions=[.695, .697, .7],
        colors=["#000000", "#6D6A99", "#C2AAE4"])

    mix_stars = sky_mat.create_mix_rgb(blend_type="ADD")
    mix_stars2 = sky_mat.create_mix_rgb(blend_type="ADD")
    stars2_noise["Color"].to(stars2_cr["Fac"])
    stars3_noise["Color"].to(stars3_cr["Fac"])
    stars2_cr[0].to(mix_stars[1])
    stars_cr[0].to(mix_stars[2])
    mix_stars[0].to(mix_stars2[1])
    stars3_cr[0].to(mix_stars2[2])

    clouds_noise = sky_mat.create_musgrave_texture(
        scale=60, detail=100, dimension=0, noise_dimensions="4D",
        musgrave_type="HETERO_TERRAIN")
    clouds_noise_cr = sky_mat.create_color_ramp(
        colors=["#032040", "#06599F", "#8CDDEE"],
        positions=[0, .95, 1], interpolation="B_SPLINE")
    clouds_noise_intensity = sky_mat.create_operation(
        operation="MULTIPLY", value=20)
    clouds_noise_intensity2 = sky_mat.create_operation(
        operation="POWER", value=1.9)
    hue_saturation = sky_mat.create_hue_saturation(saturation=1.5)

    # clouds_grad[0].to(clouds_noise["Vector"])
    clouds_noise[0].to(clouds_noise_cr["Fac"])
    clouds_noise_cr[0].to(clouds_noise_intensity[0])
    clouds_noise_intensity[0].to(clouds_noise_intensity2[0])

    mix_stars_cosmos = sky_mat.create_mix_rgb(fac=.99)
    mix_stars_clouds = sky_mat.create_mix_rgb(fac=.1)
    mix_color = sky_mat.create_mix_rgb(fac=.003)

    mix_stars2["Color"].to(mix_stars_cosmos[2])
    cosmos_noise["Fac"].to(cosmos_cr["Fac"])
    cosmos_cr["Color"].to(mix_stars_cosmos[1])

    mix_stars_cosmos[0].to(mix_color[1])
    clouds_noise_cr[0].to(mix_color[2])
    mix_color[0].to(hue_saturation["Color"])
    hue_saturation[0].to(bsdf["Emission"])

    stars_light_cr["Color"].to(stars_shine_mix[1])
    stars_cr["Color"].to(stars_shine_mix[2])
    stars_shine_mix[0].to(stars_light_intensity[0])

    stars_light_intensity[0].to(mix_stars_clouds[1])
    clouds_noise_intensity2[0].to(mix_stars_clouds[2])
    mix_stars_clouds[0].to(bsdf["Emission Strength"])
    return sky_mat


def create_black_hole_mat():
    mat = RefractionBSDF(color="#FFFFFF", roughness=0)
    layer_weight = mat.create_layer_weight(blend=.9)
    mix_shader = mat.create_mix_shader()
    cr = mat.create_color_ramp(positions=[.85, .95])
    op = mat.create_operation("POWER", -1)

    layer_weight["Facing"].to(op[0])
    op[0].to(mat.bsdf["IOR"])
    cr["Color"].to(mix_shader["Fac"])
    mat.bsdf[0].to(mix_shader[2])
    layer_weight["Facing"].to(cr["Fac"])
    mix_shader[0].to(mat.material_output["Surface"])
    return mat


def create_smoke_mat():
    mat = EmissionMaterial(color="#FFFFFF")
    transparent = mat.create_transparent_bsdf()
    mix_shader = mat.create_mix_shader()
    bsdf = mat.bsdf

    texcoord, mapping = mat.create_texture_coordinate()
    mult = mat.create_operation()
    strength = mat.create_operation("POWER", value=2)
    grad = mat.create_gradient_texture("SPHERICAL")
    grad_cr = mat.create_color_ramp(positions=[0.2, 1])
    texcoord["Object"].to(mapping["Vector"])
    mapping["Scale"] = (.13, .13, 1.2)
    mapping["Vector"].to(grad["Vector"])
    grad[0].to(grad_cr["Fac"])

    wave = mat.create_wave_texture(scale=2,
                                   wave_type="RINGS",
                                   distortion=5, detail_roughness=.1,
                                   rings_direction="SPHERICAL",
                                   detail_scale=3)
    # wave2 = mat.create_wave_texture(scale=1,
    #                                 wave_type="RINGS",
    #                                 distortion=2,
    #                                 rings_direction="SPHERICAL",
    #                                 detail_scale=8)
    # noise = mat.create_noise_texture(scale=30)
    noise_cr = mat.create_color_ramp()
    mapping["Vector"].to(wave["Vector"])
    # wave[0].to(noise["Vector"])
    # wave2[0].to(wave["Vector"])
    wave[0].to(noise_cr["Fac"])
    noise_cr[0].to(bsdf["Color"])

    grad_cr[0].to(mult[0])
    noise_cr[0].to(mult[1])
    mult[0].to(strength[0])
    strength[0].to(bsdf["Strength"])

    mat.material_output["Surface"].unlink()
    bsdf[0].to(mix_shader[1])
    transparent[0].to(mix_shader[2])
    grad_cr[0].to(mix_shader["Fac"])
    mix_shader[0].to(mat.material_output["Volume"])
    # transparent[0].to(mat.material_output["Volume"])

    # grad = mat.create_gradient_texture("SPHERICAL")
    # grad_cr = mat.create_color_ramp(positions=[.6, .8])
    # texcoord, mapping = mat.create_texture_coordinate()
    # texcoord["Object"].to(mapping["Vector"])
    # mapping[0].to(grad["Vector"])
    # grad[0].to(grad_cr["Fac"])

    # smoke_color = mat.create_noise_texture()
    # smoke_color_cr = mat.create_color_ramp(
    #     colors=["#9C3317", "#F6C050"])
    # smoke_color["Fac"].to(smoke_color_cr["Fac"])
    # mix_rgb = mat.create_mix_rgb(blend_type="MULTIPLY")
    # smoke_color_cr["Color"].to(mix_rgb[1])
    # grad["Color"].to(mix_rgb[2])

    # # mix_rgb[0].to(bsdf["Emission"])

    # grad_cr[0].to(bsdf["Emission"])
    # grad_cr[0].to(bsdf["Emission Strength"])

    # smoke = mat.create_noise_texture()
    # smoke_cr = mat.create_color_ramp()
    # smoke["Fac"].to(smoke_cr["Fac"])
    # smoke_cr["Color"].to(bsdf["Emission Strength"])
    return mat
