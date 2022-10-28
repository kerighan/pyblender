def add_effects(scene):
    compositor = scene.create_compositor()
    
    glare = compositor.create_glare(size=7, mix=1)
    distort = compositor.create_lens_distortion(distortion=.0, dispersion=.03)
    cc = compositor.create_color_correction(contrast=1.,
                                            saturation=1.04)

    compositor.input["Image"].to(glare["Image"])
    glare["Image"].to(distort["Image"])
    distort["Image"].to(cc["Image"])
    cc["Image"].to(compositor.output["Image"])
