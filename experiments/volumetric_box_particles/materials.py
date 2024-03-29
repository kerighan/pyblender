from pyblender.animation import linear
from pyblender.material import (EmissionMaterial, Material, RefractionBSDF,
                                VolumeMaterial)


def create_sun_mat():
    mat = EmissionMaterial(color="#F916D7")
    bsdf = mat.bsdf
    texcoord = mat.create_texture_coordinate(False)
    mapping = mat.create_mapping()
    normalize = mat.create_vector_math("NORMALIZE")
    musgrave = mat.create_musgrave_texture(
        musgrave_type="MULTIFRACTAL", scale=1, detail=7,
        dimension=0., lacunarity=2.1)
    add = mat.create_mix_rgb("ADD", fac=1)
    subtract = mat.create_mix_rgb("SUBTRACT", fac=1)
    multiply = mat.create_mix_rgb("MULTIPLY", fac=1)
    fade = mat.create_operation("MULTIPLY", value=.4)
    power = mat.create_operation("POWER", value=3.3)
    noise = mat.create_noise_texture(
        scale=2, detail=9.8, roughness=.492, noise_dimensions="4D")
    value = mat.create_value(value=2)

    mapping["Scale"] = (1, 1, 2)
    texcoord["Object"].to(normalize["Vector"])
    normalize[0].to(mapping["Vector"])
    mapping["Vector"].to(noise["Vector"])
    noise["Color"].to(subtract[1])
    subtract[0].to(multiply[1])
    value[0].to(multiply[2])
    multiply[0].to(add[2])
    texcoord["Object"].to(add[1])
    add["Color"].to(musgrave["Vector"])
    musgrave[0].to(fade[0])
    fade[0].to(power[0])
    power[0].to(bsdf["Strength"])
    return mat


def create_text_mat():
    mat = Material(color="#000000")
    return mat


def create_accretion_disk():
    mat = VolumeMaterial(density=2)
    bsdf = mat.bsdf
    mix_rgb = mat.create_mix_rgb(blend_type="MULTIPLY", fac=1)
    colorization = mat.create_color_ramp(
        positions=[0, .3, .36, .45, .5, .6],
        colors=["#000000", "#001635", "#1731A9",
                "#268AFC",  "#7EBDEE", "#FFFFFF"],
        interpolation="EASE")
    # hues= .5, .93, .17, .33
    saturation = mat.create_hue_saturation(saturation=1.2, hue=.5)
    density = mat.create_operation(value=50)
    density_cr = mat.create_color_ramp(positions=[.4, 1])
    emission = mat.create_operation("MULTIPLY", value=100)
    emission_cr = mat.create_color_ramp(
        colors=["#000000", "#DDDDDD", "#FFFFFF"],
        positions=[0, .95, 1], interpolation="EASE")

    # gradient falloff
    falloff_gradient = mat.create_gradient_texture("SPHERICAL")
    accretion_cr = mat.create_color_ramp(positions=[.5, .75],
                                         interpolation="B_SPLINE")
    texcoord, mapping = mat.create_texture_coordinate()
    texcoord["Object"].to(mapping["Vector"])
    mapping["Vector"].to(falloff_gradient["Vector"])
    falloff_gradient["Color"].to(accretion_cr["Fac"])
    falloff_gradient["Fac"].to(density_cr["Fac"])
    falloff_gradient["Fac"].to(emission_cr["Fac"])
    # density
    density_cr[0].to(density[0])
    density[0].to(bsdf["Density"])
    # emission
    emission_cr[0].to(emission[0])
    emission[0].to(bsdf["Emission Strength"])

    # accretion texture
    noise = mat.create_noise_texture(scale=5, detail=32,
                                     noise_dimensions="4D")
    smaller_noise = mat.create_noise_texture(scale=32, detail=32)
    smallest_noise = mat.create_noise_texture(scale=64, detail=32)
    mix_noise = mat.create_mix_rgb(blend_type="OVERLAY", fac=1)
    mix_noise2 = mat.create_mix_rgb(blend_type="OVERLAY", fac=1)
    gradient = mat.create_gradient_texture("SPHERICAL")
    texcoord, mapping = mat.create_texture_coordinate()
    accretion_rgb = mat.create_mix_rgb(fac=.2)
    texcoord["Object"].to(mapping["Vector"])
    mapping["Vector"].to(gradient["Vector"])
    mapping["Scale"] = (1, 1, .1)
    gradient["Color"].to(accretion_rgb[1])
    mapping["Vector"].to(accretion_rgb[2])
    accretion_rgb["Color"].to(smallest_noise["Vector"])
    accretion_rgb["Color"].to(smaller_noise["Vector"])
    accretion_rgb["Color"].to(noise["Vector"])
    smaller_noise["Fac"].to(mix_noise2[1])
    smallest_noise["Fac"].to(mix_noise2[2])
    noise["Fac"].to(mix_noise[1])
    mix_noise2["Color"].to(mix_noise[2])

    # mix rgb
    accretion_cr["Color"].to(mix_rgb[1])
    mix_noise["Color"].to(mix_rgb[2])
    mix_rgb[0].to(colorization["Fac"])
    colorization[0].to(saturation["Color"])
    saturation[0].to(bsdf["Emission Color"])

    # noise.animate("W", *linear([0, .1], [1, 96]))
    return mat


def create_black_hole():
    mat = RefractionBSDF(roughness=0)
    bsdf = mat.bsdf
    # mix_shader = mat.create_mix_shader()
    # mix_shader[0].to(mat.material_output["Surface"])

    # surface blackness
    layer_weight = mat.create_layer_weight(blend=.96)
    layer_weight_cr = mat.create_color_ramp(positions=[.6, 1])
    layer_weight_op = mat.create_operation("POWER", value=-1)
    layer_weight["Facing"].to(layer_weight_cr["Fac"])
    layer_weight_cr["Color"].to(layer_weight_op[0])
    layer_weight_op[0].to(bsdf["IOR"])

    return mat


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

    mix_stars_cosmos = sky_mat.create_mix_rgb(fac=.997)
    mix_stars_clouds = sky_mat.create_mix_rgb(fac=.1)
    mix_color = sky_mat.create_mix_rgb(fac=.002)

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
    mat = RefractionBSDF(color="#FFFFFF", roughness=0.6)
    layer_weight = mat.create_layer_weight(blend=.65)
    mix_shader = mat.create_mix_shader()
    cr = mat.create_color_ramp(positions=[.86-.1, .99-.1])
    op = mat.create_operation("POWER", -.05)

    layer_weight["Facing"].to(op[0])
    op[0].to(mat.bsdf["IOR"])
    cr["Color"].to(mat.bsdf["Roughness"])
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
