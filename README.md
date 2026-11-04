# pyblender

Script Blender scenes and motion graphics from plain Python. pyblender is a thin,
declarative layer over `bpy`: meshes, lights, materials, cameras, keyframes, 3D text
with staggered motions, particles, compositor post-processing (glitches, glow, grain)
and PNG / MP4 export, without touching the Blender UI.

```python
import pyblender as pb
from pyblender import motion

title = pb.Text("HELLO", size=1.2, extrude=0.2, bevel=0.02, split="letters",
                material=pb.Material(color="#F7F7F2", roughness=0.3))
motion.pop_in(title, start=0, duration=15, stagger=3, easing="back-out")
motion.pop_out(title, start=80, reverse=True)

pb.Sun(energy=4, focus_point=(0, 0, 0))
camera = pb.Camera((0, -10, 1)).look_at((0, 0, 0.3))

scene = pb.Scene(camera)
scene.post.vignette(0.4)
scene.post.glitch(bursts=[(40, 48)])
scene.set_animation_bounds(0, 100)
scene.render("hello.mp4", fast=True, size=(1280, 720))
```

```bash
pyblender hello.py        # runs the script inside Blender, writes hello.mp4
```

---

## Contents

1. [Installation](#installation)
2. [Running a script](#running-a-script)
3. [Concepts](#concepts)
4. [API reference](#api-reference)
   [Scene](#scene) · [Camera](#camera) · [Lights](#lights) · [Meshes](#meshes) ·
   [Materials](#materials) · [Modifiers, particles, forces](#modifiers-particles-and-forces) ·
   [Text](#text) · [Motion](#motion) · [Post-processing](#post-processing) ·
   [Timeline and easings](#timeline-and-easings)
5. [Examples](#examples)
6. [Recipes](#recipes)
7. [Troubleshooting](#troubleshooting)
8. [Limitations](#limitations)

---

## Installation

Requirements:

| Dependency | Why | Notes |
|---|---|---|
| Blender 3.x (tested with 3.1.2) | provides `bpy`, the renderer | binary download is enough, no install |
| numpy | inside Blender's Python | bundled with Blender |
| ffmpeg | MP4 export | `apt install ffmpeg` |
| a CUDA / OptiX GPU | optional, speeds up Cycles | falls back to CPU automatically |

Install the package in any Python environment to get the `pyblender` command:

```bash
cd pyblender
pip install -e .
```

Tell it where Blender is if it is not on your `PATH`:

```bash
export BLENDER=/path/to/blender-3.1.2-linux-x64/blender
```

The `pyblender` command adds the package to Blender's own Python path at launch, so
nothing has to be installed into Blender's bundled Python.

## Running a script

A pyblender script is a normal Python file that runs **inside Blender**, in background
mode. Three equivalent ways:

```bash
# 1. the pyblender command (recommended)
pyblender my_scene.py

# 2. blender directly, with the repository root on the path
blender -b --python-expr "import sys; sys.path.insert(0, '/path/to/pyblender')" --python my_scene.py

# 3. after installing pyblender into Blender's bundled Python
/path/to/blender/3.1/python/bin/python3.10 -m pip install -e /path/to/pyblender
blender -b --python my_scene.py
```

Relative paths in the script (fonts, textures, `render("renders/x.mp4")`) are resolved
from the directory you launch the command from.

## Concepts

**Empty scene.** Importing `pyblender` resets Blender to an empty scene: no default
cube, light or camera. The script contains everything that is rendered.

**Objects.** Every class that creates something in the scene (`Cube`, `Sun`, `Camera`,
`Text`…) wraps a `bpy` object available as `.obj`, and shares the same base API:

| Member | Role |
|---|---|
| `location`, `rotation`, `scale` | read / write properties |
| `look_at(point_or_object)` | orient towards a point `(x, y, z)`, or track another object (follows it when animated) |
| `set_visible(bool)` | hide in viewport and render |
| `animate_location(values, frames)` | one keyframe per value |
| `animate_rotation(values, frames)` | Euler angles in radians |
| `animate_scale(values, frames)` | |
| `animate_rotation_z(values, frames)`, `animate_scale_z(values, frames)` | single axis, scalar values |
| `animate(attribute, values, frames, data=None, index=-1)` | keyframe any RNA property |

**Keyframes.** All animation uses the same convention: a list of `values` and a list of
`frames` of the same length (`frames` defaults to `0, 1, 2…`). Values are keyframed
exactly, so you control the easing by computing the values (see
[Timeline and easings](#timeline-and-easings)). Before the first keyframe and after the
last one, Blender holds the value.

**Units and axes.** Blender units, Z is up. A text or a title card is typically placed
at the origin, standing in the XZ plane, with the camera on -Y looking at it:
`pb.Camera((0, -10, 0)).look_at((0, 0, 0))`.

**Colors** are hex strings `"#FF8800"` or `(r, g, b)` floats in `[0, 1]`.

**Rendering.** `fast=True` uses Eevee (seconds per frame), `fast=False` uses Cycles
(path tracing, physically accurate, slower). Most motion-graphics work is fine in Eevee.

---

## API reference

Everything below is importable from `pyblender` directly (`pb.Cube`) unless a module
is named.

### Scene

```python
scene = pb.Scene(camera)
```

| Method | Description |
|---|---|
| `render(filename, size=(1280, 720), fast=True, gpu=True, samples=None, frame_rate=30, crf=18)` | Render. `.png` gives a still (or an image sequence in `filename/` when it ends with `/` and bounds are set), `.mp4` renders the animation and encodes it with ffmpeg. `samples` overrides the engine default (Eevee 64, Cycles 128). `crf` is the H.264 quality, lower is better. Returns the absolute path. |
| `set_animation_bounds(start, end)` | Frame range, required for `.mp4` and image sequences. |
| `add_bloom(intensity=0.05, radius=2, threshold=0.8)` | Eevee bloom: bright and emissive surfaces glow. |
| `add_volumetric_light(shadows=True)` | Eevee volumetrics, needed to see a `VolumeMaterial` (fog, god rays). |
| `set_gravity((0, 0, -9.81))` | Scene gravity for particles. |
| `use_gpu(device_type="CUDA")` | Cycles on GPU (`"CUDA"` or `"OPTIX"`), warns and falls back to CPU if unavailable. Called automatically by `render(gpu=True)`. |
| `post` | The [post-processing](#post-processing) stack. |
| `scene` | The underlying `bpy.types.Scene` for anything not covered. |

### Camera

```python
pb.Camera(location=(0, 0, 0), focus_point=None, aperture_fstop=2.8, aperture_ratio=1.0,
          aperture_blades=8, lens=50)
```

`lens` is the focal length in mm. Passing `focus_point=(x, y, z)` enables depth of field
focused there; lower `aperture_fstop` (1.4, 0.5…) blurs more. Point it with
`look_at(...)` and move it with `animate_location(...)`.

### Lights

| Class | Signature | Notes |
|---|---|---|
| `Sun` | `Sun(energy=5, color=None, rotation=None, focus_point=None, location=(0, 0, 10))` | Directional. `focus_point` sets the direction. Energy in W/m², 3–10 is daylight. |
| `PointLight` | `PointLight(location, energy=50, color=None, radius=0.1)` | Omnidirectional. Energy in W, hundreds to thousands for a lit room. `radius` softens shadows. |
| `SpotLight` | `SpotLight(location, energy=50, color=None, rotation=None, focus_point=None, size=0.785, blend=0.15, radius=0.1)` | `size` is the cone angle in radians, `blend` the edge softness in `[0, 1]`. |

All lights have `animate_energy(values, frames)` and expose the light datablock as `.data`.

### Meshes

| Class | Signature |
|---|---|
| `Cube` | `Cube(location, rotation, scale=(1, 1, 1), size=1, material=None, visible=True)` |
| `Plane` | `Plane(location, rotation, scale, size=1, material, visible)` |
| `Grid` | `Grid(location, rotation, scale, size=1, width=10, height=10, material, visible)` — `width`/`height` are subdivisions |
| `Sphere` | `Sphere(location, radius=1, div=32, material, visible, smooth=True)` |
| `IcoSphere` | `IcoSphere(location, radius=1, div=3, material, visible, smooth=True)` |
| `Cylinder` | `Cylinder(location, rotation, scale, radius=1, depth=1, div=32, material, visible)` |
| `Line` | `Line(points, stroke_width=0.01, material, visible)` — a polyline rendered as a tube |
| `Empty` | `Empty(location, name="empty")` — invisible, for focus or tracking targets and grouping |

Meshes add `set_material(material)` and `set_smooth(bool)`.

### Materials

```python
pb.Material(color="#FFFFFF", roughness=0.5, metallic=0.5, specular=0.0, opacity=1.0,
            emission_strength=0.0, emission_color=None, texture=None, cast_shadows=True)
```

A Principled BSDF. `opacity < 1` makes glass-like transmission. `emission_strength > 0`
makes the surface glow (use `scene.add_bloom()` or `scene.post.glow()` to see halos).
`texture` is a `pb.Image("file.jpg")` used as base color.
`material.animate_color(colors, frames)` keyframes the base color.

```python
pb.VolumeMaterial(color="#FFFFFF", density=1.0, emission_strength=0.0, emission_color=None)
```

Fog or smoke; assign it to a closed mesh (a big cube) enclosing the scene.

`Material` is a `NodeMaterial`, so you can extend it with shader nodes:

```python
mat = pb.Material()
noise = mat.add_noise_texture(scale=5)
ramp = mat.add_color_ramp(colors=["#FF0000", "#00FF00"])
mat.link(noise, ramp, "Fac", "Fac")
mat.link(ramp, mat.bsdf, "Color", "Base Color")
mat.add_node("ShaderNodeBump")                       # any bpy node type
```

Helpers: `add_node(type, **props)`, `add_math(operation, value)`, `add_color_ramp(colors)`,
`add_noise_texture(scale, detail, roughness)`, `add_image_texture(image)`,
`link(source, target, output, input)`. `mat.bsdf` and `mat.output` are the default nodes.

### Modifiers, particles and forces

| Class | Signature | Notes |
|---|---|---|
| `Displacement` | `Displacement(mesh, image, strength=1.0, midlevel=0.5)` | Height map. The mesh needs vertices: use a `Grid` with many subdivisions or add a `Subdivision`. |
| `Subdivision` | `Subdivision(mesh, levels=2, smooth=True)` | |
| `ParticleSystem` | `ParticleSystem(emitter, instance, count=500, frames=(1, 200), lifetime=100, size=0.2, gravity=1.0, velocity_random=0, size_random=0, lifetime_random=0, rotation_random=0, phase_random=0, angular_velocity=0, time_tweak=1, hide_emitter=True)` | Emits copies of `instance` from the faces of `emitter`. Keep `instance` far away or hidden. Do not pass `visible=False` to the emitter, it would hide the particles too. |
| `Vortex`, `Turbulence` | `(location, strength=1, noise=0, flow=0)` | Force fields acting on particles. |

### Text

```python
pb.Text(body, size=1.0, extrude=0.0, bevel=0.0, font=None, material=None,
        location=(0, 0, 0), rotation=None, upright=True, align="center", tracking=0.0,
        line_spacing=1.0, split=None, visible=True)
```

| Parameter | Description |
|---|---|
| `body` | The string, `\n` for a new line (single object only). |
| `size`, `extrude`, `bevel` | Letter height, 3D depth, edge rounding. |
| `font` | Path to a `.ttf` / `.otf`. `None` uses Blender's built-in font. On Linux try `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`. |
| `upright` | Stand the text in the XZ plane facing -Y (default). `upright=False` lays it flat on XY. `rotation` overrides both. |
| `align` | `"left"`, `"center"` or `"right"` relative to `location`. The origin is on the baseline. |
| `tracking` | Extra letter spacing, as a fraction of `size`. |
| `split` | `None`: one object. `"letters"` or `"words"`: one object per part, parented to an invisible group. |

A split text exposes its parts in `text.parts` (iterable, `len(text)`), each a `TextObject`
with `.body` and `.width`. Motions animate the parts; `text.animate_location(...)` and the
other base methods move the whole group. `text.width` is the total width.

### Motion

`pyblender.motion` provides staggered animations for a split `Text` or any list of objects.
Every function keyframes one channel per part, starting at `start` and delaying each part
by `stagger` frames:

| Function | Channel | Signature |
|---|---|---|
| `pop_in` | scale | `(items, start=0, duration=15, stagger=2, easing="back-out", scale_from=0)` |
| `pop_out` | scale | `(items, start=0, duration=15, stagger=2, easing="back-in", scale_to=0)` then hides |
| `slide_in` | location | `(items, offset=(0, -1, 0), start=0, duration=20, stagger=2, easing="cubic-out")` hidden before |
| `slide_out` | location | `(items, offset=(0, 1, 0), start=0, duration=20, stagger=2, easing="cubic-in")` then hides |
| `flip_in` | rotation | `(items, angle=(pi/2, 0, 0), start=0, duration=20, stagger=2, easing="back-out")` hidden before |
| `flip_out` | rotation | `(items, angle=(-pi/2, 0, 0), start=0, duration=20, stagger=2, easing="back-in")` then hides |
| `typewriter` | visibility | `(items, start=0, stagger=3)` |
| `wave` | location | `(items, start=0, end=60, amplitude=0.2, period=30, phase=0.6, axis=1)` |
| `shake` | location | `(items, start=0, end=30, amplitude=0.05, seed=0)` decaying jitter |

All `*_in` / `*_out` functions accept `reverse=True` to stagger from the last part.
Offsets and angles are in the parent's local space: for an upright text, local Y is up,
so `slide_in(offset=(0, -1, 0))` rises from below.

Motions on different channels combine freely. Two motions on the same channel of the
same part overwrite each other where their frames overlap. `motion.schedule(...)` yields
`(part, frames, progress)` to write your own.

### Post-processing

`scene.post` is a stack of compositor effects applied to the rendered image, in the
order they are added. Each method returns an `Effect` with named parameters:

```python
post = scene.post
post.vignette(0.4)
glow = post.glow(threshold=1.0, mix=0.2)
glow.set("mix", 0.4)                                   # change a value
post.chromatic_aberration().animate("amount", [0, 0.5, 0], [40, 44, 50])  # keyframe it
post.roll().burst("y", bursts=[(60, 70)], low=-200, high=200)              # random per frame
post.glitch(bursts=[(40, 52), (90, 96)], strength=1.0, seed=0)             # preset
```

| Effect | Parameters | Description |
|---|---|---|
| `rgb_split(x=0, y=0)` | `x`, `y` (pixels) | Red and blue channels shifted in opposite directions. |
| `chromatic_aberration(amount=0, distort=0)` | `amount`, `distort` | Lens dispersion fringes and barrel distortion, `[0, 1]`. |
| `slices(strength=0, coverage=0.3, size=0.15, seed=0)` | `strength` (pixels), `coverage`, `offset` | Horizontal bands shifted sideways with wrap-around. Animate `offset` to make bands jump. |
| `grain(amount=0)` | `amount` | Film grain, different on every frame. |
| `scanlines(amount=0, density=200)` | `amount` | CRT lines. |
| `vignette(amount=0, size=0.9, softness=0.4)` | `amount` | Darkened corners. |
| `glow(threshold=1, mix=0, size=7, kind="FOG_GLOW", streaks=4)` | `mix`, `threshold` | Glare. `kind`: `FOG_GLOW`, `STREAKS`, `GHOSTS`, `SIMPLE_STAR`. `mix` in `[-1, 1]`. |
| `roll(y=0, x=0)` | `x`, `y` (pixels) | Whole picture shifted with wrap-around, VHS style. |
| `color(hue=0.5, saturation=1, value=1)` | `hue`, `saturation`, `value` | Hue rotation (0.5 neutral) and multipliers. |
| `exposure(stops=0)` | `stops` | Brightness in stops, for flickers. |
| `blur(size=0)` | `size` | Gaussian blur relative to the frame width. |
| `pixelate(size=4)` | none | Blocky pixels. Static. |
| `glitch(bursts, strength=1, seed=0)` | returns `[rgb_split, slices, grain, exposure]` | Sci-fi screen glitch during each `(start, end)` range, nothing outside. |

`Effect` methods: `set(name, value)`, `animate(name, values, frames)`,
`burst(name, bursts, low, high, seed=0, rest=0)`.

### Timeline and easings

`pyblender.animation` is pure Python (no `bpy`) and helps compute the `values` lists.

```python
from pyblender.animation import Timeline, Cycle, EASINGS, tween

tl = Timeline(0, 30, 60)                       # keyframe times, any unit
tl.z = [("cubic-in-out", 0, 2), ("cubic-in-out", 2, 0)]
tl.color = [("linear", "#FF0000", "#0000FF"), ("constant", "#0000FF")]
tl[15].z            # 1.0
tl[45].color        # array([0., 0., 1.])

cube.animate_location([(0, 0, tl[f].z) for f in range(60)])
tween("back-out", 0, 10, 0.5)                  # single interpolation
```

Each attribute takes one entry per segment: `(easing, start, end)` or `(easing, value)`
for a constant. Hex colors interpolate as RGB. `tl.delay(n)` shifts a copy, `tl.before`
and `tl.after` set values outside the range, `tl.dtype["n"] = int` casts, `Cycle` loops.

Easing names: `linear`, `quad|cubic|quart|quint|exp|sine|circ` with `-in`, `-out`,
`-in-out`, plus the motion-design ones `back-in`, `back-out`, `back-in-out`,
`elastic-out`, `bounce-out` (these overshoot).

---

## Examples

Run them from the `examples/` directory; outputs go to `examples/renders/` (not
versioned, render them locally).

```bash
cd examples
pyblender text_motion.py
```

| Script | Output | Shows |
|---|---|---|
| `text_motion.py` | mp4 | Title card: letters pop in, words slide in, wave, exit. |
| `glitch_title.py` | mp4 | Sci-fi title with CRT look, chromatic aberration and glitch bursts. |
| `wave_grid.py` | mp4 | 576 cubes rippling like water, seamless loop. |
| `lissajous.py` | mp4 | Glowing curve, lights racing along it, orbiting camera tracking an `Empty`. |
| `fireflies.py` | mp4 | Emissive particles in fog with volumetric light and bloom. |
| `glass_spheres.py` | png | Matte, metal and glass spheres on a `Timeline` gradient, Cycles with depth of field. |
| `maelstrom.py` | mp4 | Hundreds of animated cubes with bloom. |
| `volumetric.py` | png | Spot light through fog, Cycles. |
| `heightmap.py` | png | `Grid` displaced by an image. |
| `particles.py` | mp4 | `ParticleSystem` and `Turbulence`, animated light. |
| `node_material.py` | png | Procedural material with noise, color ramp and displacement. |

Render times on an RTX 2070 at 720p: 10 s to 2 min per example.

## Recipes

**Preview a few frames instead of the whole video.** Set the frame and render a still:

```python
scene.set_animation_bounds(0, 149)
for frame in (10, 60, 120):
    scene.scene.frame_set(frame)
    scene.render(f"preview_{frame}.png", size=(640, 360), samples=8)
```

**Seamless loop.** Make every periodic motion complete a whole number of periods in
`N_FRAMES` and render frames `0 .. N_FRAMES - 1` (see `wave_grid.py`, `lissajous.py`).

**Animate a text as a block and its letters individually.**

```python
title = pb.Text("HELLO", split="letters")
motion.pop_in(title)                                        # letters
title.animate_location([(0, 0, 0), (0, 0, 2)], [0, 60])     # whole group
```

**Camera that keeps looking at a moving target.** `camera.look_at(target)` with an
object adds a tracking constraint; animate either of them.

**Sub-frame control of an easing.** Compute values with `EASINGS[name](t)` on a numpy
array and feed them to `animate_*`.

**Anything pyblender does not expose.** Every wrapper gives you the `bpy` object:
`cube.obj`, `light.data`, `material.mat`, `scene.scene`, `scene.post.tree`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError: pyblender` | The script runs in Blender's Python. Use the `pyblender` command, or add the repository to `sys.path` before importing (see [Running a script](#running-a-script)). |
| `Blender executable not found` | Set `BLENDER=/path/to/blender` or add it to `PATH`. |
| Black or empty render | No light, or the camera does not face the objects. Add a `Sun(focus_point=...)` and check `camera.look_at`. |
| Particles invisible | The emitter was created with `visible=False`, which also hides its particles. Let `ParticleSystem(hide_emitter=True)` hide it. |
| Fog invisible in Eevee | Call `scene.add_volumetric_light()`. |
| Text appears flat / from above | `Text` is upright by default; put the camera on -Y. Use `upright=False` for a flat text. |
| Letters already visible before their motion | Use the motion functions (they hide parts before `*_in` and after `*_out`), or keyframe `hide_render` yourself. |
| `GPU rendering unavailable` warning | Cycles falls back to CPU. Check the driver, or pass `gpu=False` to silence it. |
| Eevee fails in a headless server | Eevee needs an OpenGL context. Use `fast=False` (Cycles) or a virtual display (`xvfb-run`). |
| Overlapping letters with `split="letters"` | Kerning is lost between separate objects. Increase `tracking` or use a bold font. |

## Limitations

- `split` text supports a single line.
- `pixelate` is not animatable.
- No per-letter fade (alpha) yet: letters share the material.
- Tested with Blender 3.1. Blender 4.x renamed Eevee (`BLENDER_EEVEE_NEXT`) and some
  Principled BSDF sockets (`Specular` → `Specular IOR Level`, `Emission` → `Emission Color`);
  `scene.py` and `material.py` are the two files to adapt.
