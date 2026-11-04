class ParticleSystem:
    """Emit instances of ``instance`` from the faces of ``emitter``.

    Arguments:
        emitter: the mesh particles are emitted from.
        instance: the mesh rendered at every particle.
        count: number of particles.
        frames: ``(start, end)`` emission range in frames.
        lifetime: particle lifetime in frames.
        size: particle size multiplier.
        gravity: gravity weight, 0 disables it.
        velocity_random: randomize the initial velocity.
        size_random, lifetime_random, rotation_random, phase_random: randomization in [0, 1].
        angular_velocity: angular velocity factor.
        time_tweak: simulation speed multiplier.
        hide_emitter: hide the emitter mesh at render time.
    """

    def __init__(
        self,
        emitter,
        instance,
        count=500,
        frames=(1, 200),
        lifetime=100,
        size=0.2,
        gravity=1.0,
        velocity_random=0.0,
        size_random=0.0,
        lifetime_random=0.0,
        rotation_random=0.0,
        phase_random=0.0,
        angular_velocity=0.0,
        time_tweak=1.0,
        hide_emitter=True,
    ):
        obj = emitter.obj
        self.modifier = obj.modifiers.new("particles", type="PARTICLE_SYSTEM")
        self.settings = settings = obj.particle_systems[-1].settings

        settings.count = count
        settings.frame_start, settings.frame_end = frames
        settings.lifetime = lifetime
        settings.lifetime_random = lifetime_random
        settings.emit_from = "FACE"
        settings.distribution = "JIT"
        settings.physics_type = "NEWTON"
        settings.render_type = "OBJECT"
        settings.instance_object = instance.obj
        settings.particle_size = size
        settings.size_random = size_random
        settings.factor_random = velocity_random
        settings.use_rotations = True
        settings.use_dynamic_rotation = True
        settings.rotation_factor_random = rotation_random
        settings.phase_factor_random = phase_random
        settings.angular_velocity_factor = angular_velocity
        settings.time_tweak = time_tweak
        settings.effector_weights.gravity = gravity

        if hide_emitter:
            obj.show_instancer_for_render = False
