"""Particle systems: emitted instances or hair."""


class ParticleSystem:
    """Emit instances of ``instance`` from ``emitter``, or grow hair on it.

    Arguments:
        emitter: the mesh particles are emitted from.
        instance: the mesh rendered at every particle (``None`` renders nothing / hair only).
        count: number of particles.
        frames: ``(start, end)`` emission range in frames.
        lifetime: particle lifetime in frames.
        size: particle size multiplier.
        velocity: initial speed along the emitter normals.
        gravity: gravity weight, 0 disables it.
        emit_from: ``"FACE"``, ``"VERT"`` or ``"VOLUME"``.
        velocity_random, size_random, lifetime_random, rotation_random, phase_random:
            randomization in [0, 1].
        angular_velocity, brownian: angular velocity factor and brownian motion.
        time_tweak: simulation speed multiplier.
        hair: grow hair instead of emitting; ``hair_length`` is then the strand length.
        material: index of the emitter material slot used for the particles.
        hide_emitter: hide the emitter mesh at render time.
    """

    def __init__(self, emitter, instance=None, count=500, frames=(1, 200), lifetime=100, size=0.2,
                 velocity=1.0, gravity=1.0, emit_from="FACE", velocity_random=0.0,
                 size_random=0.0, lifetime_random=0.0, rotation_random=0.0, phase_random=0.0,
                 angular_velocity=0.0, brownian=0.0, time_tweak=1.0, hair=False,
                 hair_length=0.25, hair_steps=5, children="NONE", material=1,
                 use_modifier_stack=False, hide_emitter=True):
        obj = emitter.obj
        self.modifier = obj.modifiers.new("particles", type="PARTICLE_SYSTEM")
        self.system = obj.particle_systems[-1]
        self.settings = settings = self.system.settings

        settings.count = count
        settings.frame_start, settings.frame_end = frames
        settings.lifetime = lifetime
        settings.lifetime_random = lifetime_random
        settings.emit_from = emit_from
        settings.distribution = "JIT"
        settings.physics_type = "NEWTON"
        settings.particle_size = size
        settings.size_random = size_random
        settings.normal_factor = velocity
        settings.factor_random = velocity_random
        settings.brownian_factor = brownian
        settings.use_rotations = True
        settings.use_dynamic_rotation = True
        settings.rotation_factor_random = rotation_random
        settings.phase_factor_random = phase_random
        settings.angular_velocity_factor = angular_velocity
        settings.time_tweak = time_tweak
        settings.effector_weights.gravity = gravity
        settings.child_type = children
        settings.material = material
        settings.use_modifier_stack = use_modifier_stack

        if instance is not None:
            settings.render_type = "OBJECT"
            settings.instance_object = instance.obj
        if hair:
            settings.type = "HAIR"
            settings.hair_length = hair_length
            settings.hair_step = hair_steps
            settings.use_advanced_hair = True
            settings.use_hair_bspline = True
            self.system.use_hair_dynamics = True
            if instance is None:
                settings.render_type = "PATH"
        if hide_emitter:
            obj.show_instancer_for_render = False


Particles = ParticleSystem
