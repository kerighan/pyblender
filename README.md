# pyblender

Script Blender scenes and motion graphics from plain Python. pyblender is a declarative
layer over `bpy`: meshes and imported models, lights, cameras, node materials with a
one-line linking idiom, geometry nodes, modifiers and physics, keyframes, 3D text with
staggered motions, particles, compositor post-processing (glitches, glow, grain) and
PNG / MP4 export, without touching the Blender UI.

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
   [Modifiers and physics](#modifiers-and-physics) · [Materials and nodes](#materials-and-nodes) ·
   [Geometry nodes](#geometry-nodes) · [Textures](#textures) · [Curves](#curves) ·
   [Particles and forces](#particles-and-forces) · [Text](#text) · [Motion](#motion) ·
   [Post-processing](#post-processing) · [Timeline and easings](#timeline-and-easings)
5. [Examples](#examples)
6. [Recipes](#recipes)
7. [Migrating from the 2022 API](#migrating-from-the-2022-api)
8. [Troubleshooting](#troubleshooting)

---

## Installation

| Dependency | Why | Notes |
|---|---|---|
| Blender 3.x (tested with 3.1.2) | provides `bpy`, the renderer | binary download is enough |
| numpy | inside Blender's Python | bundled with Blender |
| ffmpeg | MP4 export | `apt install ffmpeg` |
| a CUDA / OptiX GPU | optional, speeds up Cycles | falls back to CPU automatically |

Install the package in any Python environment to get the `pyblender` command:

```bash
cd pyblender
pip install -e .
export BLENDER=/path/to/blender-3.1.2-linux-x64/blender   # if blender is not on PATH
```

The `pyblender` command adds the package to Blender's own Python path at launch, so
nothing has to be installed into Blender's bundled Python.

## Running a script

A pyblender script is a normal Python file that runs **inside Blender**, in background
mode:

```bash
pyblender my_scene.py                      # recommended
blender -b --python-expr "import sys; sys.path.insert(0, '/path/to/pyblender')" --python my_scene.py
```

Relative paths in the script (fonts, textures, models, `render("renders/x.mp4")`) are
resolved from the directory you launch the command from.

## Concepts

**Empty scene.** Importing `pyblender` resets Blender to an empty scene. The script
contains everything that is rendered.

**Objects.** Every class that creates something in the scene wraps a `bpy` object
available as `.obj` and shares one base API:

| Member | Role |
|---|---|
| `location`, `rotation`, `scale` | read / write properties (`rotation` in degrees) |
| `translate(x, y, z)`, `rotate(x, y, z)`, `resize(factor)` | relative transforms |
| `look_at(point_or_object)` | orient towards a point, or track an object (follows it when animated) |
| `set_visible(bool)`, `set_ray_visibility(camera=…, shadow=…)` | visibility, Cycles ray visibility |
| `set_parent(obj)`, `select()` | hierarchy, selection for `bpy.ops` |
| `animate_location / animate_rotation / animate_scale(values, frames)` | one keyframe per value |
| `animate_rotation_z`, `animate_scale_z`, `animate_visibility` | single channel |
| `animate(attribute, values, frames, data=None)` | keyframe any RNA property |
| `set_interpolation("LINEAR", extrapolation="LINEAR")`, `repeat_animation(count)` | fcurve tweaks |

**Degrees.** Every rotation (`rotation=`, `rotate()`, `animate_rotation`, motion
angles, spot `angle`) is in degrees.

**Keyframes.** All animation uses the same convention: a list of `values` and a list of
`frames` of the same length (`frames` defaults to `0, 1, 2…`). Values are keyframed
exactly, so you control the easing by computing the values, with
[Timeline and easings](#timeline-and-easings) or numpy. Blender holds the first value
before the first keyframe and the last one after.

**Nodes.** Materials, geometry nodes and the compositor share one idiom: sockets are
attributes, `>>` links, arithmetic creates Math nodes. See
[Materials and nodes](#materials-and-nodes).

**Groups.** A split text or a multi-object model is a group: `.parts` lists the objects,
`.obj` is an empty parenting them, so transforms and keyframes on the wrapper move the
whole group.

**Colors** are hex strings `"#FF8800"` or `(r, g, b)` floats in `[0, 1]`. Units are
Blender units, Z is up. `fast=True` renders with Eevee, `fast=False` with Cycles.

---

## API reference

Everything below is importable from `pyblender` directly (`pb.Cube`) unless a module
is named.

### Scene

```python
scene = pb.Scene(camera=None, size=(1280, 720), fast=True, samples=None)
```

The last camera created is the active one, so `camera` is optional.

| Method | Description |
|---|---|
| `render(filename, size=None, fast=None, gpu=True, samples=None, frame_rate=30, crf=18, frame=None, bake=False)` | `.png` still (or image sequence in `filename/` when it ends with `/`), `.mp4` animation encoded with ffmpeg. `frame` renders a given frame, `bake` runs the physics caches first. Returns the absolute path. |
| `set_animation_bounds(start, end)` | Frame range, required for `.mp4` and sequences. |
| `set_frame(n)`, `set_gravity((0, 0, -9.81))` | |
| `set_background(color, strength=1, image=None)` | World color or HDRI/environment image (also lights the scene). |
| `set_color_management(view_transform="Filmic", look="None", exposure=0, gamma=1)` | `look` such as `"Medium High Contrast"`. |
| `set_eevee(ssr, refraction, gtao, motion_blur, soft_shadows, volumetric_tile_size, volumetric_samples)` | Eevee quality switches. |
| `set_motion_blur(True, shutter=0.5)`, `set_transparent(True)`, `set_freestyle(line_thickness)` | |
| `add_bloom(intensity, radius, threshold)` | Eevee bloom. |
| `add_volumetric_light(shadows=True)` | Eevee volumetrics, needed for `VolumeMaterial`. |
| `add_glare(size, mix, threshold, dispersion, saturation, contrast, gain)` | Finishing stack: dispersion + color correction + fog glow (in `post`). |
| `use_gpu("CUDA")`, `bake()` | Cycles on GPU (CPU fallback); bake physics over the animation range. |
| `post` | The [post-processing](#post-processing) stack (`compositor` is an alias). |
| `scene` | The underlying `bpy.types.Scene`. |

### Camera

```python
pb.Camera(location=(0, 0, 0), rotation=(0, 0, 0), focus_point=None, aperture_fstop=2.8,
          aperture_ratio=1.0, aperture_blades=8, lens=50, clip=(0.1, 1000))
```

`lens` is the focal length in mm. `focus_point` enables depth of field; `set_focus(target,
fstop)` does it later, on a point or an object. `animate_lens(values, frames)` zooms,
`animate_fstop` racks the aperture.

### Lights

| Class | Signature | Notes |
|---|---|---|
| `Sun` | `Sun(energy=5, color=None, rotation=None, focus_point=None, location=(0, 0, 10), angle=0.5)` | Directional. 3–10 W/m² is daylight; `angle` softens shadows. |
| `PointLight` | `PointLight(location, energy=50, color=None, radius=0.1)` | Hundreds to thousands of W for a room. |
| `SpotLight` | `SpotLight(location, energy=50, color=None, rotation=None, focus_point=None, angle=45, blend=0.15, radius=0.1)` | `angle` is the full cone in degrees. |
| `AreaLight` | `AreaLight(location, energy=100, color=None, rotation=None, focus_point=None, size=(1, 1))` | A softbox. |

All lights have `animate_energy` and `animate_color`, and expose the datablock as `.data`.

### Meshes

| Class | Signature |
|---|---|
| `Cube` (alias `Box`) | `Cube(location, rotation, scale=(1, 1, 1), size=1, material=None, visible=True)` |
| `Plane` | `Plane(location, rotation, scale, size=1, material, visible)` |
| `Grid` | `Grid(location, rotation, scale, size=1, width=10, height=10, material, visible)` — subdivisions |
| `Sphere` (alias `UVSphere`) | `Sphere(location, rotation, scale, radius=1, div=32, material, visible, smooth=True)` |
| `IcoSphere` | `IcoSphere(location, rotation, scale, radius=1, div=3, material, visible, smooth=True)` |
| `Circle` | `Circle(location, rotation, radius=1, div=32, fill=False, material, visible)` |
| `Cylinder` | `Cylinder(location, rotation, scale, radius=1, depth=1, div=32, caps="NGON", material, visible)` |
| `Cone`, `Torus` | `Cone(…, radius, depth, div)`, `Torus(…, major_radius, minor_radius, div)` |
| `Line` | `Line(points, stroke_width=0.01, material, visible)` — polyline rendered as a tube |
| `Model` | `Model(path, location, rotation, scale, material, visible)` — `.glb` / `.gltf` / `.fbx` / `.obj`; several objects become a group |
| `Empty` | `Empty(location, rotation, scale, name)` — invisible target or group |
| `merge(meshes)` | join several meshes into one object |

Mesh methods:

| Method | Description |
|---|---|
| `add_material(m)`, `set_material(m, index=0)`, `get_material(index_or_name)` | material slots; `get_material` wraps an existing material as a `NodeMaterial` (imported models) |
| `material_names` | names of the slots |
| `set_smooth(True)` (alias `shade_smooth`) | smooth shading |
| `subdivide(cuts)`, `remove_faces("up")`, `convert_to_mesh()`, `apply_modifiers()` | real geometry edits |

### Modifiers and physics

Every `add_*` returns the `bpy` modifier for further tweaking:

| Method | Description |
|---|---|
| `add_modifier(kind, **props)` | any Blender modifier by type (`"BEVEL"`, `"SOLIDIFY"`…) |
| `add_subdivision(levels, render_levels, smooth)` | subdivision surface |
| `add_displacement(texture, strength, midlevel, coordinates, direction)` | image path, `Image`, `Texture` or `Noise` as height map |
| `add_boolean(other, operation)`, `add_array(count, offset, relative, offset_object)`, `add_mirror(axis, mirror_object)` | |
| `add_wireframe(thickness)`, `add_bevel(width, segments)`, `add_solidify(thickness)`, `add_decimate(ratio)`, `add_remesh(mode, voxel_size)`, `add_smooth`, `add_ocean`, `add_wave`, `add_explode` | |
| `geometry(name)` | a Geometry Nodes modifier, see below |
| `rigid_body(kind="ACTIVE", mass, friction, bounciness, shape, damping, kinematic)` | `"ACTIVE"` falls and collides, `"PASSIVE"` is a static obstacle |
| `throw(velocity, frame)` | initial velocity of a rigid body |
| `soft_body(mass, bend, push, pull)`, `cloth(quality, mass, stiffness)`, `collision()` | |

Physics is simulated over the animation range when rendering with `bake=True` (or
`scene.bake()`).

### Materials and nodes

```python
pb.Material(color="#FFFFFF", roughness=0.5, metallic=0.5, specular=0.0, opacity=1.0,
            transmission=0.0, subsurface=0.0, emission_strength=0.0, emission_color=None,
            texture=None, normal=None, displacement=None, displacement_scale=1.0,
            cast_shadows=True, shadow_mode=None, blend_mode=None)
```

A Principled BSDF. Numeric inputs also accept an image path, an `Image` or a node.
`opacity < 1` enables alpha blending, `transmission=1` makes glass. `emission_strength`
makes the surface glow (use `scene.add_bloom()` or `scene.post.glow()` for halos).

Other presets: `DiffuseMaterial(color, roughness, texture, normal)`,
`EmissionMaterial(color, strength)`, `RefractionMaterial(color, ior, roughness)`,
`VolumeMaterial(color, density, emission_strength, anisotropy)` (fog: assign to a closed
mesh enclosing the scene).

Every material is a `NodeMaterial`: a shader node tree with `bsdf` (its main shader) and
`output`. Sockets are attributes, `>>` links, `=` sets, arithmetic creates Math nodes:

```python
mat = pb.Material(roughness=0.4)
noise = mat.create_noise_texture(scale=5)
ramp = mat.create_color_ramp(colors=["#FF0000", "#00FF00"])

noise.fac >> ramp.fac >> mat.bsdf.base_color       # a chain of links
(noise.fac * 0.1 + 0.05) >> mat.output.displacement  # Math nodes created on the fly
mat.bsdf.roughness = 0.3                             # set a socket
mat.bsdf.base_color = "#FF8800"
mat.bsdf.roughness.animate([0, 1], [0, 30])          # keyframe a socket
noise.fac.map_range((0, 1), (0, 5)).clamp(0, 2)      # helpers on a socket
noise.fac.mix("#00FF00", fac=0.3)                    # MixRGB
noise.fac.apply("SINE")                              # any Math operation
```

Socket names are matched loosely: `base_color`, `"Base Color"` and `["Base Color"]` are
the same. Without an explicit socket, `>>` uses the first output and the first input.
`a.to(b)` is the same as `a >> b`; `a.unlink()` removes incoming links.

Node factories (each returns a node): `create(type, **props)` for any `bpy` node, and
`create_principled_bsdf`, `create_diffuse_bsdf`, `create_transparent_bsdf`,
`create_glass_bsdf`, `create_refraction_bsdf`, `create_emission`, `create_volume_scatter`,
`create_volume_principled`, `create_mix_shader`, `create_add_shader`,
`create_shader_to_rgb`, `create_texture_coordinate` (returns `(coords, mapping)`),
`create_mapping`, `create_geometry`, `create_camera_data`, `create_layer_weight`,
`create_fresnel`, `create_ambient_occlusion`, `create_bevel`, `create_normal_map`,
`create_bump`, `create_displacement`, `create_hue_saturation`, `create_bright_contrast`,
`create_separate_hsv`, `create_combine_hsv`, `create_separate_rgb`, `create_combine_rgb`,
`create_texture` (image), `create_noise_texture`, `create_musgrave_texture`,
`create_voronoi_texture`, `create_wave_texture`, `create_magic_texture`,
`create_gradient_texture`, `create_checker_texture`, `create_brick_texture`,
`create_math` (alias `create_operation`), `create_vector_math`, `create_value`,
`create_rgb`, `create_mix_rgb`, `create_color_ramp`, `create_map_range`, `create_clamp`,
`create_separate_xyz`, `create_combine_xyz`.

`mat.reset()` empties the tree, `mat.set_shadows(...)`, `mat.set_displacement("BOTH")`,
`mat.mat` is the `bpy` material.

### Geometry nodes

`mesh.geometry()` adds a Geometry Nodes modifier and returns a `Geometry` tree with the
same idiom; `input` and `output` are the group boundaries:

```python
geo = pb.Cube().geometry()
sphere = geo.create_icosphere(radius=0.05)
points = geo.create_mesh_to_points()
instances = geo.create_instance_on_points()
geo.input.geometry >> points.mesh
points.points >> instances.points
sphere.mesh >> instances.instance
instances.instances >> geo.output.geometry
```

Factories: `create_cube`, `create_icosphere`, `create_uv_sphere`, `create_grid`,
`create_volume_cube` (all with `replace=True` to become the whole output),
`create_curve_line`, `create_curve_circle`, `create_object_info(obj)`,
`create_instance_on_points`, `create_mesh_to_points`, `create_distribute_points`,
`create_realize_instances`, `create_join_geometry`, `create_transform`,
`create_set_material`, `create_set_position`, `create_position`, `create_normal`,
`create_index`, `create_volume_to_mesh`, `create_mesh_boolean`,
`create_subdivision_surface`, `create_curve_to_points`, `create_curve_to_mesh`,
`create_mesh_to_curve`, `create_random_value`, `create_rotate_vector`,
`create_scene_time`, plus the shared math / value / ramp / xyz nodes.

### Textures

| Class | Use |
|---|---|
| `Image(path, color_space="sRGB")` | material textures, displacement maps, compositor inputs, `Scene.set_background(image=…)` |
| `Texture(path)` | image texture datablock for modifiers |
| `Noise(kind="DISTORTED_NOISE", scale, basis, distortion, intensity, depth)` | procedural datablock (`"CLOUDS"`, `"MARBLE"`, `"WOOD"`, `"VORONOI"`…) for `add_displacement` and `post.create_texture` |

### Curves

`Bezier(points, kind="NURBS", resolution, cyclic, stroke_width, material)` draws a smooth
curve through points, `BezierCircle(location, rotation, radius, stroke_width)` a circle.
`stroke_width > 0` renders the curve as a tube. `curve.follow(obj, frames=100)` moves an
object along the curve.

### Particles and forces

```python
pb.ParticleSystem(emitter, instance=None, count=500, frames=(1, 200), lifetime=100, size=0.2,
                  velocity=1.0, gravity=1.0, emit_from="FACE", velocity_random=0,
                  size_random=0, lifetime_random=0, rotation_random=0, phase_random=0,
                  angular_velocity=0, brownian=0, time_tweak=1, hair=False, hair_length=0.25,
                  hair_steps=5, children="NONE", material=1, hide_emitter=True)
```

Emits copies of `instance` from the faces of `emitter`, or grows hair with `hair=True`
(rendered as strands when `instance` is None). Keep `instance` far away; do not pass
`visible=False` to the emitter, it would hide the particles too. `Particles` is an alias.

Forces: `Vortex`, `Turbulence`, `Wind` (blows along its local Z, orient it with
`rotation`), `ForceField` (negative strength attracts), all with
`(location, rotation, strength, noise, flow, size, falloff)` and `animate_strength`.

### Text

```python
pb.Text(body, size=1.0, extrude=0.0, bevel=0.0, font=None, material=None,
        location=(0, 0, 0), rotation=None, upright=True, align="center", tracking=0.0,
        line_spacing=1.0, split=None, visible=True)
```

| Parameter | Description |
|---|---|
| `body` | The string, `\n` for a new line (single object only). |
| `font` | Path to a `.ttf` / `.otf`. `None` uses Blender's built-in font. On Linux try `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`. |
| `upright` | Stand the text in the XZ plane facing -Y (rotation `(90, 0, 0)`). `upright=False` lays it flat. `rotation` overrides both. |
| `align` | `"left"`, `"center"` or `"right"` relative to `location`. The origin is on the baseline. |
| `tracking` | Extra letter spacing, as a fraction of `size`. |
| `split` | `None`: one object. `"letters"` or `"words"`: one object per part, parented to an invisible group. |

A split text exposes its parts in `text.parts`, each a `TextObject` with `.body` and
`.width`; `text.width` is the total width. Motions animate the parts; the base methods
move the whole group.

### Motion

`pyblender.motion` provides staggered animations for a split `Text` or any list of objects.
Each function keyframes one channel per part, starting at `start` and delaying each part
by `stagger` frames:

| Function | Channel | Signature |
|---|---|---|
| `pop_in` | scale | `(items, start=0, duration=15, stagger=2, easing="back-out", scale_from=0)` |
| `pop_out` | scale | `(items, start=0, duration=15, stagger=2, easing="back-in", scale_to=0)` then hides |
| `slide_in` | location | `(items, offset=(0, -1, 0), start=0, duration=20, stagger=2, easing="cubic-out")` hidden before |
| `slide_out` | location | `(items, offset=(0, 1, 0), start=0, duration=20, stagger=2, easing="cubic-in")` then hides |
| `flip_in` | rotation | `(items, angle=(90, 0, 0), start=0, duration=20, stagger=2, easing="back-out")` hidden before |
| `flip_out` | rotation | `(items, angle=(-90, 0, 0), start=0, duration=20, stagger=2, easing="back-in")` then hides |
| `typewriter` | visibility | `(items, start=0, stagger=3)` |
| `wave` | location | `(items, start=0, end=60, amplitude=0.2, period=30, phase=0.6, axis=1)` |
| `shake` | location | `(items, start=0, end=30, amplitude=0.05, seed=0)` decaying jitter |

All `*_in` / `*_out` functions accept `reverse=True`. Offsets and angles are in the
parent's local space: for an upright text, local Y is up, so `slide_in(offset=(0, -1, 0))`
rises from below. Motions on different channels combine; two motions on the same channel
of the same part overwrite each other where they overlap. `motion.schedule(...)` yields
`(part, frames, progress)` to write your own.

### Post-processing

`scene.post` is a stack of compositor effects applied to the rendered image, in the
order they are added. Each method returns an `Effect` with named parameters:

```python
post = scene.post
post.vignette(0.4)
glow = post.glow(threshold=1.0, mix=0.2)
glow.set("mix", 0.4)
post.chromatic_aberration().animate("amount", [0, 0.5, 0], [40, 44, 50])
post.roll().burst("y", bursts=[(60, 70)], low=-200, high=200)
post.glitch(bursts=[(40, 52), (90, 96)], strength=1.0, seed=0)
```

| Effect | Parameters | Description |
|---|---|---|
| `rgb_split(x=0, y=0)` | `x`, `y` (pixels) | Red and blue channels shifted in opposite directions. |
| `chromatic_aberration(amount=0, distort=0)` | `amount`, `distort` | Lens dispersion and barrel distortion, `[0, 1]`. |
| `slices(strength=0, coverage=0.3, size=0.15, seed=0)` | `strength`, `coverage`, `offset` | Horizontal bands shifted sideways with wrap-around. |
| `grain(amount=0)` | `amount` | Film grain, different on every frame. |
| `scanlines(amount=0, density=200)` | `amount` | CRT lines. |
| `vignette(amount=0, size=0.9, softness=0.4)` | `amount` | Darkened corners. |
| `glow(threshold=1, mix=0, size=7, kind="FOG_GLOW", streaks=4)` | `mix`, `threshold` | Glare: `FOG_GLOW`, `STREAKS`, `GHOSTS`, `SIMPLE_STAR`. |
| `color_correction(saturation, contrast, gain, gamma, lift)` | same names | Master color correction. |
| `roll(y=0, x=0)` | `x`, `y` (pixels) | Whole picture shifted with wrap-around (VHS). |
| `color(hue=0.5, saturation=1, value=1)` | `hue`, `saturation`, `value` | Hue rotation and multipliers. |
| `exposure(stops=0)`, `blur(size=0)`, `pixelate(size=4)` | `stops`, `size`, none | |
| `glitch(bursts, strength=1, seed=0)` | returns the effects | RGB split + slices + grain + flicker during each `(start, end)`. |

`Effect` methods: `set(name, value)`, `animate(name, values, frames)`,
`burst(name, bursts, low, high, seed=0, rest=0)`.

The compositor is also a node tree with the same idiom, for hand-built graphs:
`post.input` (Render Layers), `post.output` (Composite), `post.chain(node)` inserts a
node into the effect stack, and `create_glare`, `create_lens_distortion`,
`create_color_correction`, `create_sun_beams`, `create_blur`, `create_image`,
`create_texture`, `create_hue_saturation`, `create_translate`, `create_displace`,
`create_ellipse_mask`, `create_mix_rgb`, `create_math`… build nodes.

### Timeline and easings

`pyblender.animation` is pure Python (no `bpy`) and helps compute the `values` lists.

```python
from pyblender.animation import Timeline, Cycle, EASINGS, tween, linear, shake, flicker, Movement

tl = Timeline(0, 30, 60)                       # keyframe times, any unit
tl.z = [("cubic-in-out", 0, 2), ("cubic-in-out", 2, 0)]
tl.color = [("linear", "#FF0000", "#0000FF"), ("constant", "#0000FF")]
tl[15].z            # 1.0
cube.animate_location([(0, 0, tl[f].z) for f in range(60)])

cube.animate_location(*linear((0, 0, 0), (5, 0, 0), frames=(0, 30), easing="quad-out"))
cube.animate_location(*shake((30, 60), origin=(5, 0, 0), intensity=0.2))
cube.animate_visibility(flicker(5, step_size=2))
Movement(speed=0.1, turn=True).start_at(0, 0, 0).move_to(5, 0, 0).move_to(5, 5, 0).apply(cube)
```

Each `Timeline` attribute takes one entry per segment: `(easing, start, end)` or
`(easing, value)` for a constant. Hex colors interpolate as RGB. `tl.delay(n)` shifts a
copy, `tl.before` / `tl.after` set values outside the range, `Cycle` loops.

Easing names: `linear`, `quad|cubic|quart|quint|exp|sine|circ` with `-in`, `-out`,
`-in-out`, plus `back-in`, `back-out`, `back-in-out`, `elastic-out`, `bounce-out`.

---

## Examples

Run them from the `examples/` directory; outputs go to `examples/renders/` (not
versioned, render them locally):

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
| `node_material.py` | png | Procedural material with the `>>` node idiom. |
| `maelstrom.py` | mp4 | Hundreds of animated cubes with bloom. |
| `volumetric.py` | png | Spot light through fog, Cycles. |
| `heightmap.py` | png | `Grid` displaced by an image. |
| `particles.py` | mp4 | `ParticleSystem` and `Turbulence`, animated light. |

The `experiments/` folder holds older scenes written for the 2022 API (see
[Migrating](#migrating-from-the-2022-api)).

## Recipes

**Preview frames instead of the whole video.**

```python
scene.set_animation_bounds(0, 149)
for frame in (10, 60, 120):
    scene.render(f"preview_{frame}.png", size=(640, 360), samples=8, frame=frame)
```

**Physics.** Give objects `rigid_body()`, a floor `rigid_body("PASSIVE")`, set the
animation bounds and render with `bake=True`.

**Imported model with its own materials.** `model = pb.Model("robot.glb")`, then
`model.get_material("Eyes").bsdf.emission_strength = 5`.

**Seamless loop.** Make every periodic motion complete a whole number of periods in
`N_FRAMES` and render frames `0 .. N_FRAMES - 1`.

**Camera that keeps looking at a moving target.** `camera.look_at(target)` with an
object adds a tracking constraint.

**Anything pyblender does not expose.** Every wrapper gives you the `bpy` object:
`cube.obj`, `light.data`, `material.mat`, `scene.scene`, `post.tree`, `geo.group`,
and `add_modifier(kind, **props)` / `create(node_type, **props)` reach any modifier or node.

## Migrating from the 2022 API

Most names were kept; the main changes:

| 2022 | Now |
|---|---|
| `mesh.modify_subdivide/displace/boolean/array/…()` | `mesh.add_subdivision/add_displacement/add_boolean/add_array/…()` |
| `mesh.modify_rigid_body()`, `modify_soft_body()`, `modify_collision()` | `mesh.rigid_body()`, `soft_body()`, `collision()` |
| `mesh.modify_geometry()` | `mesh.geometry()` |
| `mesh.scale(x, y, z)` | `mesh.resize((x, y, z))`; `scale` is now a property |
| `scene.create_compositor()` | `scene.post` (same `create_*` names, plus effects) |
| `node["Out"].to(other["In"])` | still works; `node.out >> other.in_` is shorter |
| `Particles(src, tgt, factor_random=…)` | `ParticleSystem(emitter, instance, velocity_random=…)`, see signature |
| `SpotLight(size=radians)` | `SpotLight(angle=degrees)` |
| `Scene.render(background_color=…, contrast=…)` | `scene.set_background()`, `scene.set_color_management()`, `scene.set_eevee()` |
| `Text(text, align="CENTER")` | `Text(body, align="center", split=…)`, upright by default |
| `camera.animate_location()` with linear extrapolation | `camera.animate_location(...).set_interpolation("LINEAR", "LINEAR")` |
| `Image`, `Texture`, `Noise` | unchanged (`pyblender.texture`) |
| `RefractionBSDF` | `RefractionMaterial` (alias kept) |

Rotations were already in degrees and still are.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError: pyblender` | Use the `pyblender` command, or add the repository to `sys.path` before importing. |
| `Blender executable not found` | Set `BLENDER=/path/to/blender` or add it to `PATH`. |
| Black or empty render | No light, or the camera does not face the objects. Add a `Sun(focus_point=…)`, check `camera.look_at`. |
| Particles invisible | The emitter was created with `visible=False`. Let `ParticleSystem(hide_emitter=True)` hide it. |
| Fog invisible in Eevee | Call `scene.add_volumetric_light()`. |
| Physics does nothing | Render with `bake=True` and set the animation bounds. |
| `cannot link nodes that belong to different node trees` | A node from one material was linked into another; create it in the target material. |
| Text appears flat / from above | `Text` is upright by default; put the camera on -Y. |
| `GPU rendering unavailable` warning | Cycles falls back to CPU. Check the driver, or pass `gpu=False`. |
| Eevee fails on a headless server | Eevee needs OpenGL. Use `fast=False` (Cycles) or `xvfb-run`. |
