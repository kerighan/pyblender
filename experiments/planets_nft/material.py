from pyblender.material import Material
from pyblender.utils import hex_to_rgba


def create_atmosphere_material():
    material = Material(roughness=.6, metallic=0.1, shadow_mode="HASHED")
    output = material.material_output
    output["Surface"].unlink()
    volume = material.create_volume_scatter()
    texcoord, mapping = material.create_texture_coordinate()
    gradient = material.create_gradient_texture(gradient_type="SPHERICAL")
    ramp = material.create_color_ramp(positions=[0, .3], interpolation="EASE")
    multiply = material.create_operation(value=2)
    mapping["Scale"] = (.92, .92, .92)
    volume["Color"] = hex_to_rgba("#89B3EB")

    texcoord["Object"].to(mapping["Vector"])
    mapping["Vector"].to(gradient["Vector"])
    gradient["Fac"].to(volume["Density"])
    gradient["Fac"].to(ramp["Fac"])
    ramp["Color"].to(multiply[0])
    multiply["Value"].to(volume["Density"])
    volume["Volume"].to(output["Volume"])
    return material


def create_clouds_material():
    material = Material(roughness=.6, metallic=0.1, shadow_mode="HASHED")
    bsdf = material.bsdf
    transparent = material.create_transparent_bsdf()
    mix_shader = material.create_mix_shader(fac=.7)
    noise = material.create_noise_texture(
        scale=5.5, detail=6.5, roughness=.62, distortion=1)

    transparent["BSDF"].to(mix_shader[1])
    bsdf["BSDF"].to(mix_shader[2])

    ramp = material.create_color_ramp(
        positions=[.54, .8], interpolation="EASE")
    noise["Fac"].to(ramp["Fac"])
    ramp["Color"].to(mix_shader["Fac"])
    mix_shader["Shader"].to(material.material_output["Surface"])
    return material


def create_planet_material():
    material = Material(roughness=.6, metallic=0.1)
    bsdf = material.bsdf

    noise = material.create_noise_texture(
        scale=2.5, detail=6, roughness=.65)
    noise_2 = material.create_noise_texture(
        scale=4.4, detail=8, roughness=.65)
    noise_3 = material.create_noise_texture(
        scale=13, detail=3, roughness=.6)
    texcoord, mapping = material.create_texture_coordinate()
    mix_rgb = material.create_mix_rgb(fac=.7, blend_type="LIGHTEN")
    ramp = material.create_color_ramp(positions=[.43, 1])
    ramp_2 = material.create_color_ramp(positions=[.6, 1])
    ramp_3 = material.create_color_ramp(
        colors=["#001111", "#2D463E", "#668F41"], interpolation="EASE",
        positions=[0, .5, 1])
    ramp_4 = material.create_color_ramp(
        colors=["#A5A5A5", "#FFFFFF"], positions=[0, .11],
        interpolation="EASE")
    ramp_5 = material.create_color_ramp()
    bump = material.create_bump(strength=.2)

    # scratches
    mapping["Scale"] = (1, 1, 18)
    mapping["Vector"].to(noise_3["Vector"])
    noise_3["Fac"].to(ramp_2["Fac"])

    noise_2["Color"].to(noise["Vector"])
    noise["Fac"].to(ramp["Fac"])

    # color map
    ramp["Color"].to(mix_rgb["Color1"])
    ramp_2["Color"].to(mix_rgb["Color2"])
    mix_rgb["Color"].to(ramp_3["Fac"])
    ramp_3["Color"].to(bsdf["Base Color"])

    # roughness map
    mix_rgb["Color"].to(ramp_4["Fac"])
    ramp_4["Color"].to(bsdf["Roughness"])

    # bump map
    mix_rgb["Color"].to(ramp_5["Fac"])
    ramp_5["Color"].to(bump["Height"])
    bump["Normal"].to(bsdf["Normal"])

    return material
