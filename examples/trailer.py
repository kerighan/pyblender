"""The pyblender trailer: ten shots, poetry and tech, in one script.

Run ``pyblender trailer.py``; shots render with Cycles one after the other (Blender is
reset between them) and are joined with crossfades and a generated soundtrack into
``renders/trailer.mp4``.
"""

import os
import wave as wavefile

import numpy as np
import pyblender as pb

# ----------------------------------------------------------------------
# Shared look
# ----------------------------------------------------------------------

FONTS = "/usr/share/fonts/truetype/dejavu/"
BOLD, REGULAR, MONO = (os.path.join(FONTS, f) if os.path.exists(os.path.join(FONTS, f)) else None
                       for f in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf", "DejaVuSansMono.ttf"))
BG, WHITE, ACCENT, CYAN, GREEN = "#0B0E14", "#F4F1EA", "#FF6B35", "#19D3FF", "#2BFF88"


def make_music(path, seconds, rate=44100, seed=0):
    """A soft ambient pad (Am, F, C, G) with sparse pentatonic pings, written as a WAV."""
    t = np.arange(int(seconds * rate)) / rate
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63),
              (261.63, 329.63, 392.0), (196.0, 246.94, 293.66)]
    out = np.zeros_like(t)
    chord_length = 6.0
    for i, chord in enumerate(chords * 4):
        start = i * chord_length
        if start >= seconds:
            break
        envelope = (np.clip((t - start) / 2.0, 0, 1)
                    * np.clip((start + chord_length + 1.5 - t) / 2.0, 0, 1))
        vibrato = 0.3 * np.sin(2 * np.pi * 0.1 * t)
        for f in chord:
            for k, amp in ((1, 1.0), (2, 0.35), (3, 0.12)):
                out += amp * envelope * np.sin(2 * np.pi * f * k * t + vibrato)
            out += 0.5 * envelope * np.sin(2 * np.pi * f * 1.003 * t)
    rng = np.random.default_rng(seed)
    for start in np.arange(1.0, seconds - 3, 1.7):
        f = rng.choice([523.25, 587.33, 659.25, 783.99, 880.0])
        d = np.clip(t - start, 0, None)
        out += 0.35 * np.exp(-d * 2.5) * np.sin(2 * np.pi * f * d) * (t >= start)
    out *= np.clip(t / 1.5, 0, 1) * 0.5 / np.abs(out).max()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wavefile.open(path, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes((out * 32767).astype(np.int16).tobytes())
    return path


MUSIC = make_music("renders/trailer_music.wav", seconds=60)
movie = pb.Movie("renders/trailer.mp4", fade=0.5, size=(1280, 720), engine="cycles", samples=48,
                 audio=MUSIC)


def caption(camera, text, start, y=-0.82, size=0.11, color=WHITE, font=None, stagger=0.06):
    """A line of text pinned to the camera, typed in at ``start`` seconds.

    ``y`` is relative to the frame height (-1 bottom edge, 1 top edge), whatever the lens.
    """
    distance = 5.0
    half_width = distance * 18 / camera.data.lens          # 36 mm sensor
    half_height = half_width * 9 / 16
    label = pb.Text(text, size=size, font=font or REGULAR, split="words", upright=False,
                    align="left", location=(-0.86 * half_width, y * half_height, -distance),
                    material=pb.Material(color=color, emission_strength=1.5, roughness=1))
    label.set_parent(camera)
    label.parts.typewriter(stagger=stagger, start=start)
    return label


def code(camera, text, start):
    return caption(camera, text, start, y=-0.92, size=0.085, color=CYAN, font=MONO, stagger=0.03)


def backdrop(color=BG, depth=6):
    pb.Plane(size=80, location=(0, depth, 0), rotation=(90, 0, 0),
             material=pb.Material(color=color, roughness=0.9, metallic=0))
    pb.Plane(size=80, location=(0, 0, -1.5), material=pb.Material(color=color, roughness=0.5,
                                                                 metallic=0))


def look(glow=0.12, threshold=1.0):
    scene = pb.scene()
    scene.set_background(BG, strength=0.2)
    scene.set_color_management("Filmic", "Medium High Contrast")
    scene.set_eevee(ssr=True, gtao=True, soft_shadows=True)
    if glow:
        pb.post.glow(threshold=threshold, mix=glow, size=6)
    pb.post.vignette(0.35, size=1.0, softness=0.5)
    pb.post.grain(0.04)
    return scene


def title_lights():
    pb.SpotLight((0, -3, 9), target=(0, 0, 0), energy=4000, color="#DDE8FF", angle=60, blend=0.6,
                 radius=1.0)
    pb.PointLight((-5, -4, 1), energy=300, color=ACCENT, radius=1.5)
    pb.PointLight((5, -4, 1), energy=200, color="#7FB7FF", radius=1.5)


# ----------------------------------------------------------------------
# Shots
# ----------------------------------------------------------------------

@movie.shot(duration=4.5)
def opening():
    """The name rises out of the fog, one letter at a time."""
    backdrop()
    pb.Cube(size=16, location=(0, 2, 4), material=pb.VolumeMaterial(color="#9DB4C0", density=0.08))
    title = pb.Text("pyblender", size=1.3, extrude=0.25, bevel=0.03, font=BOLD, split="letters",
                    tracking=0.02, material=pb.Material(color=WHITE, roughness=0.35, metallic=0.15))
    title.parts.wait(0.4).flip_in(angle=(-90, 0, 0), duration=0.9, stagger=0.09)
    title.parts.wait(0.3).wave(duration=2.0, amplitude=0.04, period=1.5, phase=0.4)
    title_lights()
    camera = pb.Camera((0, -13, 0.8), target=(0, 0, 0.3), lens=50)
    camera.to(location=(0, -10, 0.6), duration=4.5, easing="sine-in-out")
    caption(camera, "a Python layer over Blender", start=2.4)
    look().add_volumetric_light()


@movie.shot(duration=5)
def wave():
    """Tech: a field of cubes rippling like water, from a dozen lines of Python."""
    n, frames = 26, pb.to_frames(5)
    t = np.linspace(0, 4 * np.pi, frames, endpoint=False)
    material = pb.Material(color="#2A6FDB", roughness=0.25, metallic=0.3)
    for i in range(n):
        for j in range(n):
            x, y = i - n / 2 + 0.5, j - n / 2 + 0.5
            heights = 1 + 0.8 * np.sin(t - 0.7 * np.hypot(x, y))
            cube = pb.Cube(location=(x, y, 0), scale=(0.85, 0.85, 1), material=material)
            cube.animate_scale_z(heights, range(frames))
            cube.animate_location([(x, y, h / 2) for h in heights], range(frames))
    pb.Plane(size=200, location=(0, 0, -0.01), material=pb.Material(color="#0B1626", roughness=0.9))
    pb.Sun(energy=4, target=(0, 0, 0), location=(10, -20, 30))
    pb.PointLight((0, 0, 12), energy=4000, color="#FFD9A0", radius=3)
    camera = pb.Camera((n, -n, n * 0.75), target=(0, 0, 0), lens=45)
    camera.to(location=(n * 0.6, -n * 1.1, n * 0.35), duration=5, easing="sine-in-out")
    caption(camera, "676 cubes, one loop", start=0.8)
    code(camera, "cube.animate_scale_z(heights)", start=1.6)
    look(glow=0).set_background(BG, strength=0.3)


@movie.shot(duration=5)
def curve():
    """Poetry: a curve of light, three sparks racing along it."""
    count, frames = 600, pb.to_frames(5)
    u = np.linspace(0, 2 * np.pi, count, endpoint=False)
    points = [(3 * np.sin(3 * a), 3 * np.sin(2 * a), 2 * np.sin(5 * a)) for a in u]
    pb.Line(points + points[:1], stroke_width=0.03,
            material=pb.Material(color=CYAN, emission_strength=6))
    for k, color in enumerate(["#FF4D6D", "#FFD166", "#8AFF80"]):
        runner = pb.Sphere(radius=0.12, segments=16,
                           material=pb.Material(color=color, emission_strength=20))
        offset = k * count // 3
        runner.animate_location([points[(offset + f * count // frames) % count]
                                 for f in range(frames)], range(frames))
    camera = pb.Camera((9, 0, 3), lens=40).look_at(pb.Empty((0, 0, 0)))
    orbit = np.linspace(0, 2 * np.pi * 0.8, frames)
    camera.animate_location([(9 * np.cos(a), 9 * np.sin(a), 3 + np.sin(2 * a)) for a in orbit],
                            range(frames))
    caption(camera, "draw with light", start=1.0)
    look(glow=0.3)


@movie.shot(duration=5, bake=True)
def physics():
    """Tech: rigid bodies drop and settle."""
    floor = pb.Plane(size=40, material=pb.Material(color="#1A1E26", roughness=0.6, metallic=0))
    floor.rigid_body("PASSIVE", shape="BOX", bounciness=0.3)
    cubes = pb.Group(
        pb.Cube(location=(x * 1.1, y * 1.1, 4 + ((x + y) % 3)), rotation=(x * 25, y * 20, 0),
                size=0.8, material=pb.Material(color=(0.95, 0.35 + 0.1 * y, 0.2 + 0.1 * x),
                                               roughness=0.3))
        for x in range(-2, 3) for y in range(-2, 3))
    for cube in cubes:
        cube.rigid_body(mass=1, bounciness=0.45, friction=0.6, shape="BOX")
    pb.Sun(energy=4, angle=3, target=(0, 0, 0), location=(6, -8, 12))
    pb.AreaLight((-6, -6, 6), energy=900, size=(4, 4), target=(0, 0, 0))
    pb.SpotLight((6, 2, 8), target=(0, 0, 0), energy=1500, color="#7FB7FF", angle=50)
    camera = pb.Camera((11, -11, 7), target=(0, 0, 1), lens=45, focus=True, aperture_fstop=4)
    camera.to(location=(8, -12, 4), duration=5, easing="sine-in-out")
    caption(camera, "physics, one line per object", start=1.2)
    code(camera, "cube.rigid_body(mass=1, bounciness=0.45)", start=2.0)
    look(glow=0)


@movie.shot(duration=4.5)
def fireflies():
    """Poetry: fireflies drifting through fog under a single shaft of light."""
    firefly = pb.Sphere(location=(0, 0, 1000), radius=0.04, segments=12,
                        material=pb.Material(color="#FFE066", emission_strength=40))
    emitter = pb.Cube(location=(0, 0, 1.5), scale=(4, 4, 1.5))
    pb.ParticleSystem(emitter, firefly, count=300, frames=(0, 1), lifetime=1000, size=1,
                      gravity=0, velocity_random=0.4, size_random=0.5, time_tweak=0.3)
    pb.Turbulence(location=(0, 0, 1.5), strength=4, flow=1, noise=1)
    pb.Cube(location=(0, 0, 3), size=14, material=pb.VolumeMaterial(color="#9DB4C0", density=0.12))
    pb.Plane(size=40, material=pb.Material(color="#1F2A1F", roughness=0.95, metallic=0))
    spot = pb.SpotLight((2, -2, 9), target=(0, 0, 0), energy=3000, color="#CFE3FF", angle=35,
                        blend=0.3, radius=0.5)
    spot.to(energy=2000, duration=2.25).to(energy=3000, duration=2.25)
    camera = pb.Camera((7, -7, 2.2), target=(0, 0, 1.2), lens=35)
    camera.to(location=(5, -8, 1.6), duration=4.5, easing="sine-in-out")
    caption(camera, "three hundred fireflies", start=1.4)
    look(glow=0.3, threshold=2).add_volumetric_light()


@movie.shot(duration=4.5)
def material():
    """Tech: a procedural material built with the node idiom, its parameters tweened live."""
    mat = pb.Material(roughness=0.25, metallic=0.1)
    noise = mat.create_noise_texture(scale=3, detail=4, dimensions="4D")
    ramp = mat.create_color_ramp(colors=[BG, ACCENT, "#FFD166", WHITE],
                                 positions=[0.3, 0.5, 0.65, 0.9])
    bump = mat.create_bump(strength=0.4)
    noise.fac >> ramp.fac >> mat.bsdf.base_color
    noise.fac >> bump.height
    bump.normal >> mat.bsdf.normal
    noise.w.to(2.5, duration=4.5, easing="linear")        # the 4th dimension morphs the noise
    pb.Sphere(radius=1.6, segments=96, material=mat).to(rotation=(0, 0, 25), duration=4.5,
                                                         easing="linear")
    backdrop(depth=5)
    pb.AreaLight((-4, -5, 5), energy=1200, size=(4, 4), target=(0, 0, 0), color="#FFF1E0")
    pb.PointLight((5, -3, 2), energy=400, color="#7FB7FF", radius=1)
    camera = pb.Camera((0.5, -8, 1.0), target=pb.Empty((0, 0, 0)), lens=50)
    camera.to(location=(-1.5, -7.8, 0.4), duration=4.5, easing="sine-in-out")
    caption(camera, "shader nodes that read like Python", start=0.6)
    code(camera, "noise.fac >> ramp.fac >> bsdf.base_color", start=1.4)
    look(glow=0)


@movie.shot(duration=4.5)
def geometry():
    """Tech: geometry nodes with the same idiom, points growing over a sphere."""
    base = pb.IcoSphere(radius=1.5, subdivisions=4,
                        material=pb.Material(color="#141A24", roughness=0.6, metallic=0.2))
    geo = base.geometry()
    points = geo.create_distribute_points(density=0, seed=3)
    dots = geo.create_icosphere(radius=0.07, subdivisions=2)
    instances = geo.create_instance_on_points()
    sizes = geo.create_random_value(minimum=0.4, maximum=1.6, seed=1)
    painted = geo.create_set_material(pb.Material(color=ACCENT, roughness=0.3,
                                                  emission_strength=0.8))
    joined = geo.create_join_geometry()
    geo.output.unlink("Geometry")
    geo.input.geometry >> points.mesh
    points.points >> instances.points
    dots.mesh >> instances.instance
    sizes[1] >> instances.scale
    instances.instances >> painted.geometry
    painted.geometry >> joined.geometry
    geo.input.geometry >> joined.geometry
    joined.geometry >> geo.output.geometry
    points.density.to(30, duration=3.0, easing="quad-out")
    base.to(rotation=(0, 0, 80), duration=4.5, easing="linear")
    backdrop(depth=5)
    pb.AreaLight((-4, -5, 5), energy=1000, size=(4, 4), target=(0, 0, 0))
    pb.PointLight((5, -3, 2), energy=300, color="#7FB7FF", radius=1)
    camera = pb.Camera((0.5, -7.5, 1.2), target=pb.Empty((0, 0, 0)), lens=50)
    camera.to(location=(-1.2, -7.4, 0.5), duration=4.5, easing="sine-in-out")
    caption(camera, "geometry nodes, same idiom", start=0.6)
    code(camera, "points.points >> instances.points", start=1.4)
    look(glow=0.1)


@movie.shot(duration=4.5)
def dance():
    """A model imported with its animation: the astronaut dances."""
    model = pb.Model("../experiments/astronaut/model/Ymca Dance.fbx")
    model.set_material(pb.Material(color=WHITE, roughness=0.45, metallic=0.05))
    model.set_smooth()
    backdrop(depth=4)
    pb.SpotLight((2, -5, 5), target=(0, 0, 1), energy=2500, color="#FFE8D0", angle=50, blend=0.5,
                 radius=0.8)
    pb.SpotLight((-3, 3, 4), target=(0, 0, 1), energy=1500, color=CYAN, angle=60, blend=0.6)
    pb.PointLight((3, -2, 0.5), energy=150, color=ACCENT, radius=1)
    camera = pb.Camera((2.4, -4.2, 1.4), target=pb.Empty((0, 0, 0.95)), lens=50)
    camera.to(location=(-2.0, -4.4, 1.2), duration=4.5, easing="sine-in-out")
    caption(camera, "import a model, its animation comes along", start=0.8)
    code(camera, 'pb.Model("Ymca Dance.fbx")', start=1.6)
    look(glow=0)


@movie.shot(duration=5.5)
def glitch():
    """Tech turning into poetry: the screen breaks, then the message comes through clean."""
    backdrop(color="#0D1117")
    failure = pb.Text("SYSTEM FAILURE", size=1.0, extrude=0.2, bevel=0.02, font=BOLD,
                      split="letters", material=pb.Material(color="#F0F4FF", roughness=0.3,
                                                            emission_strength=0.4))
    failure.parts.wait(0.2).flip_in(duration=0.4, stagger=0.05)
    failure.parts.wait(1.0).shake(amplitude=0.06, duration=0.6)
    failure.parts.pop_out(duration=0.25, stagger=0.02, easing="quint-in")
    message = pb.Text("made with pyblender", size=0.75, extrude=0.15, bevel=0.02, font=BOLD,
                      split="words", location=(0, 0, -0.1),
                      material=pb.Material(color=GREEN, emission_strength=2.5))
    message.parts.wait(3.1).slide_in(offset=(0, -0.4, 0), duration=0.5, stagger=0.12)
    pb.SpotLight((3, -7, 5), target=(0, 0, 0), energy=2500, color="#DDE8FF", angle=57, blend=0.5)
    pb.PointLight((-5, -3, 2), energy=400, color=GREEN, radius=1)
    camera = pb.Camera((0, -11, 0.4), target=(0, 0, 0.1), lens=50)
    camera.to(location=(0, -10, 0.3), duration=5.5, easing="sine-in-out")
    look()
    pb.post.scanlines(0.2, density=180)
    pb.post.glow(threshold=0.8, mix=0.2)
    pb.post.chromatic_aberration(0.02).animate(
        "amount", [0.02, 0.4, 0.02, 0.0], [pb.to_frames(t) for t in (1.9, 2.3, 2.9, 3.4)])
    pb.post.glitch(bursts=[(0.1, 0.5), (1.9, 2.9)], strength=1.0, seed=3)


@movie.shot(duration=5)
def closing():
    """The name, the link, fade to black."""
    backdrop()
    title = pb.Text("pyblender", size=1.3, extrude=0.25, bevel=0.03, font=BOLD, split="letters",
                    tracking=0.02, material=pb.Material(color=WHITE, roughness=0.35, metallic=0.15))
    title.parts.wait(0.3).pop_in(duration=0.6, stagger=0.06)
    link = pb.Text("github.com/kerighan/pyblender", size=0.32, font=MONO, split="letters",
                   location=(0, 0, -0.8), material=pb.Material(color=ACCENT, emission_strength=1.5))
    link.parts.wait(1.3).typewriter(stagger=0.04)
    title_lights()
    camera = pb.Camera((0, -11, 0.5), target=(0, 0, 0.2), lens=50)
    camera.to(location=(0, -10.5, 0.4), duration=5, easing="sine-in-out")
    look()
    pb.post.exposure().animate("stops", [0, 0, -12], [pb.to_frames(t) for t in (0, 4.0, 5.0)])


if __name__ == "__main__":
    movie.render()
