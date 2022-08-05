from numpy import multiply
from pyblender.material import Material
from pyblender.utils import hex_to_rgba

# COLORS = ["#001111", "#2D463E", "#668F41"]
# CLOUD_COLOR = "#FFFFFF"
# ATMOSPHERE_COLOR = "#89B3EB"
# ATMOSPHERE_SIZE = .9
# CLOUDY = [.54, .8]  # very cloudy
# MOUNTAINS = .0
# MOUNTAINS_SCALE = 1.5
# MOUNTAINS_VOLUME = 1
# CLOUD_DISTORTION = 1

# COLORS = ["#C46221", "#F8C546", "#D8B26B"]
# CLOUD_COLOR = "#888888"  # polluted
# ATMOSPHERE_COLOR = "#858B75"
# ATMOSPHERE_SIZE = .9
# CLOUDY = [.42, .7]  # very cloudy
# CLOUD_DISTORTION = .5
# MOUNTAINS = .9
# MOUNTAINS_SCALE = 1.5
# MOUNTAINS_VOLUME = 1

# COLORS = ["#AFB39C", "#F0F3F1", "#9DBCB7"]
# CLOUD_COLOR = "#546A60"
# ATMOSPHERE_COLOR = "#252728"
# ATMOSPHERE_SIZE = .9
# CLOUDY = [.7, .8]  # very clear
# CLOUD_DISTORTION = 2
# MOUNTAINS = .9
# MOUNTAINS_SCALE = 1.5
# MOUNTAINS_VOLUME = 2


# COLORS = ["#263942", "#2E2F38", "#DB995D"]
# COLORS = ["#54416B", "#C04AC0", "#B290AC"]
# CLOUD_COLOR = "#FFFFFF"
# ATMOSPHERE_COLOR = "#E157E2"
# ATMOSPHERE_SIZE = .9
# CLOUDY = [.5, .8]  # very clear
# CLOUD_DISTORTION = 1
# MOUNTAINS = .1
# MOUNTAINS_SCALE = 1.1
# MOUNTAINS_VOLUME = 1


COLORS = ["#263942", "#2E2F38", "#DB995D"]
# COLORS = ["#54416B", "#C04AC0", "#B290AC"]
CLOUD_COLOR = "#FFFFFF"
ATMOSPHERE_COLOR = "#E157E2"
ATMOSPHERE_SIZE = .91
CLOUDY = [.7, .8]  # very clear
CLOUD_DISTORTION = 1
MOUNTAINS = .0
MOUNTAINS_SCALE = 1.1
MOUNTAINS_VOLUME = 1


def create_atmosphere_material():
    material = Material(roughness=.6, metallic=0.1, shadow_mode="HASHED")
    output = material.material_output
    output["Surface"].unlink()
    volume = material.create_volume_scatter()
    texcoord, mapping = material.create_texture_coordinate()
    gradient = material.create_gradient_texture(gradient_type="SPHERICAL")
    ramp = material.create_color_ramp(positions=[0, .3], interpolation="EASE")
    multiply = material.create_operation(value=2)
    mapping["Scale"] = (ATMOSPHERE_SIZE, ATMOSPHERE_SIZE, ATMOSPHERE_SIZE)
    volume["Color"] = hex_to_rgba(ATMOSPHERE_COLOR)

    texcoord["Object"].to(mapping["Vector"])
    mapping["Vector"].to(gradient["Vector"])
    gradient["Fac"].to(volume["Density"])
    gradient["Fac"].to(ramp["Fac"])
    ramp["Color"].to(multiply[0])
    multiply["Value"].to(volume["Density"])
    volume["Volume"].to(output["Volume"])
    return material


def create_clouds_material():
    material = Material(
        color=CLOUD_COLOR,
        roughness=.6, metallic=0.1, shadow_mode="HASHED")
    bsdf = material.bsdf
    transparent = material.create_transparent_bsdf()
    mix_shader = material.create_mix_shader(fac=.7)
    noise = material.create_noise_texture(
        scale=5.5, detail=6.5, roughness=.62, distortion=CLOUD_DISTORTION)

    transparent["BSDF"].to(mix_shader[1])
    # transparent["Color"] = hex_to_rgba(CLOUD_COLOR)
    bsdf["BSDF"].to(mix_shader[2])

    ramp = material.create_color_ramp(
        positions=CLOUDY, interpolation="EASE")
    noise["Fac"].to(ramp["Fac"])
    ramp["Color"].to(mix_shader["Fac"])
    mix_shader["Shader"].to(material.material_output["Surface"])
    return material


def create_clouds2_material():
    material = Material(
        color=COLORS[0],
        roughness=.6, metallic=0.1, shadow_mode="HASHED")
    bsdf = material.bsdf
    transparent = material.create_transparent_bsdf()
    mix_shader = material.create_mix_shader(fac=.7)
    noise = material.create_noise_texture(
        scale=2, detail=12)
    noise2 = material.create_voronoi_texture(
        scale=8)

    # transparent["Color"] = hex_to_rgba(CLOUD_COLOR)

    transparent["BSDF"].to(mix_shader[1])
    bsdf["BSDF"].to(mix_shader[2])

    ramp = material.create_color_ramp(
        positions=[.5, .7], interpolation="EASE")
    noise2[0].to(noise["Vector"])
    noise[0].to(ramp["Fac"])
    ramp["Color"].to(mix_shader["Fac"])
    mix_shader["Shader"].to(material.material_output["Surface"])
    return material


def create_planet_material():
    material = Material(roughness=.6, metallic=0.5, displace=True)
    bsdf = material.bsdf

    noise = material.create_noise_texture(
        scale=2.5, detail=6, roughness=.65)
    noise = material.create_voronoi_texture(
        scale=8, distance="CHEBYCHEV")
    noise_2 = material.create_noise_texture(
        scale=4.4, detail=8, roughness=.65)
    noise_3 = material.create_noise_texture(
        scale=13, detail=3, roughness=.6)
    noise_4 = material.create_wave_texture(
        scale=MOUNTAINS_VOLUME, detail_roughness=.1)
    noise_5 = material.create_noise_texture(scale=MOUNTAINS_SCALE, detail=12)

    _, mapping = material.create_texture_coordinate()
    mix_rgb = material.create_mix_rgb(fac=.9, blend_type="LIGHTEN")
    mix_rgb2 = material.create_mix_rgb(fac=1-MOUNTAINS, blend_type="MULTIPLY")
    ramp = material.create_color_ramp(positions=[.43, 1])
    ramp_2 = material.create_color_ramp(positions=[.6, 1])
    ramp_3 = material.create_color_ramp(
        colors=COLORS, interpolation="EASE",
        positions=[0, .5, 1])
    ramp_4 = material.create_color_ramp(
        colors=["#A5A5A5", "#FFFFFF"], positions=[0, .11],
        interpolation="EASE")
    ramp_5 = material.create_color_ramp()
    bump = material.create_bump(strength=.2)

    noise_4["Color"].to(mix_rgb2["Color1"])

    # scratches
    mapping["Scale"] = (1, 1, 18)
    mapping["Vector"].to(noise_3["Vector"])
    noise_3["Fac"].to(ramp_2["Fac"])

    noise_2["Color"].to(noise["Vector"])
    noise["Color"].to(ramp["Fac"])

    # color map
    ramp["Color"].to(mix_rgb["Color1"])

    noise_5["Fac"].to(noise_4["Vector"])
    noise_4["Color"].to(mix_rgb2["Color1"])
    mix_rgb["Color"].to(mix_rgb2["Color2"])
    ramp_2["Color"].to(mix_rgb["Color2"])
    mix_rgb2["Color"].to(ramp_3["Fac"])

    ramp_3["Color"].to(bsdf["Base Color"])

    # roughness map
    mix_rgb["Color"].to(ramp_4["Fac"])
    ramp_4["Color"].to(bsdf["Roughness"])

    # bump map
    mix_rgb2["Color"].to(ramp_5["Fac"])

    # ramp_5["Color"].to(mix_rgb3[1])
    # multiply[0].to(mix_rgb3[2])

    ramp_5["Color"].to(bump["Height"])
    bump["Normal"].to(bsdf["Normal"])

    return material


def create_planet2_material():
    material = Material(roughness=.6, metallic=0.1)
    bsdf = material.bsdf

    noise = material.create_noise_texture(
        scale=2.5, detail=6, roughness=.65)
    noise_2 = material.create_noise_texture(
        scale=4.4, detail=8, roughness=.65)
    noise_3 = material.create_noise_texture(
        scale=13, detail=3, roughness=.6)
    _, mapping = material.create_texture_coordinate()
    mix_rgb = material.create_mix_rgb(fac=.9, blend_type="LIGHTEN")
    ramp = material.create_color_ramp(positions=[.43, 1])
    ramp_2 = material.create_color_ramp(positions=[.6, 1])
    ramp_3 = material.create_color_ramp(
        colors=COLORS, interpolation="EASE",
        positions=[0, .5, 1])
    ramp_4 = material.create_color_ramp(
        colors=["#A5A5A5", "#FFFFFF"], positions=[0, .11],
        interpolation="EASE")
    ramp_5 = material.create_color_ramp()
    bump = material.create_bump(strength=.22)

    # scratches
    mapping["Scale"] = (1, 1, 18)
    mapping["Vector"].to(noise_3["Vector"])
    noise_3["Fac"].to(ramp_2["Fac"])

    noise_2["Color"].to(noise["Vector"])
    noise["Color"].to(ramp["Fac"])

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
