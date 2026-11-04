# pyblender

Script Blender scenes and motion graphics from plain Python. pyblender is a declarative
layer over `bpy`: meshes and imported models, lights, cameras, node materials with a
one-line linking idiom, geometry nodes, modifiers and physics, tweens with easing, 3D
text with staggered motions, particles, compositor post-processing (glitches, glow,
grain) and PNG / MP4 export, without touching the Blender UI.

```python
import pyblender as pb

title = pb.Text("HELLO", size=1.2, extrude=0.2, bevel=0.02, split="letters", material="#F7F7F2")
title.parts.pop_in(stagger=0.1).wait(1).wave(duration=1.5).pop_out(stagger=0.07, reverse=True)

cube = pb.Cube(location=(0, 0, -1.5), material=pb.Material(color="#FF5500", roughness=0.3))
cube.to(rotation=(0, 0, 360), duration=4, easing="linear")

pb.post.vignette(0.4).glitch(bursts=[(1.3, 1.6)])
pb.render("hello.mp4", duration=4)          # auto camera and light, Eevee, 1280x720, 30 fps
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
   [Quick start helpers](#quick-start-helpers) · [Scene](#scene) · [Camera](#camera) ·
   [Lights](#lights) · [Meshes](#meshes) · [Modifiers and physics](#modifiers-and-physics) ·
   [Tweens](#tweens) · [Groups and motions](#groups-and-motions) ·
   [Materials and nodes](#materials-and-nodes) · [Geometry nodes](#geometry-nodes) ·
   [Textures](#textures) · [Curves](#curves) · [Particles and forces](#particles-and-forces) ·
   [Text](#text) · [Post-processing](#post-processing) · [Movies](#movies) ·
   [Timeline and easings](#timeline-and-easings)
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

**Three levels of control.** `pb.render("out.png")` renders with an automatic camera and
light; `pb.scene()` gives the default `Scene` to tune it; `Scene(camera)` gives full
control. The same goes for everything: a color where a material is expected, a
`Material(...)` for the common parameters, `mat.bsdf.clearcoat = 0.5` for any socket,
`mat.create("ShaderNodeBevel")` for any node, and `.obj` / `.mat` / `.scene` for raw `bpy`.

**Objects.** Every class that creates something in the scene wraps a `bpy` object
available as `.obj` and shares one base API:

| Member | Role |
|---|---|
| `location`, `rotation`, `scale` | read / write properties (`rotation` in degrees) |
| `translate(x, y, z)`, `rotate(x, y, z)`, `resize(factor)` | relative transforms |
| `look_at(point_or_object)` | orient towards a point, or track an object |
| `to(...)`, `from_(...)`, `wait(n)` | [tweens](#tweens) with a playhead |
| `set(**props)` | set any property of the wrapper, the object or its datablock |
| `set_visible(bool)`, `hide_until(frame)`, `hide_from(frame)`, `set_ray_visibility(...)` | visibility |
| `set_parent(obj)`, `select()` | hierarchy, selection for `bpy.ops` |
| `animate_location / rotation / scale / visibility(values, frames)`, `animate(attr, values, frames)` | raw keyframes |
| `set_interpolation("LINEAR", extrapolation="LINEAR")`, `repeat_animation(count)` | fcurve tweaks |

**Degrees and seconds.** Every rotation (`rotation=`, `rotate()`, tweens, motions, spot
`angle`) is in degrees. Every time of the high-level API (tween `duration`, `start`,
`stagger`, `wait`, motions, bursts, `render(duration=)`) is in **seconds**, converted
with `pb.defaults.fps` (30): changing the frame rate keeps animations the same length.
`pb.frames(15)` forces an exact frame count. Only the raw `animate_*` methods and
`Timeline` work in frames.

**Nodes.** Materials, geometry nodes and the compositor share one idiom: sockets are
attributes, `>>` links, arithmetic creates Math nodes, `.to(value)` tweens a socket.

**Groups.** A `Group` is a list of objects that behaves like one, with staggered tweens
and the ready-made motions. A split text or a multi-object model exposes one as `.parts`.

**Colors** are hex strings `"#FF8800"` or `(r, g, b)` floats in `[0, 1]`. Units are
Blender units, Z is up.

---

## API reference

Everything below is importable from `pyblender` directly (`pb.Cube`) unless a module
is named.

### Quick start helpers

| Helper | Description |
|---|---|
| `pb.render(filename, **render_kwargs)` | Render the default scene. Adds a camera framing every object (`auto_camera`) and a soft sun (`auto_light`) when the scene has none. `duration=4` renders a 4-second animation. |
| `pb.scene()` | The default `Scene`, created on first use. `pb.scene().add_bloom()`, `pb.scene().set_background(...)`. |
| `pb.post` | The post-processing stack of the default scene: `pb.post.vignette(0.4)`. |
| `pb.defaults` | Package defaults: `size`, `engine` (`"eevee"` / `"cycles"`), `samples`, `fps`, `crf`, `gpu`. |
| `pb.frames(n)`, `pb.to_frames(seconds)`, `pb.to_seconds(frames)` | Time conversions. |
| `pb.auto_camera(direction=(0.6, -1, 0.5), lens=50)`, `pb.auto_light()` | The automatic camera and light, callable explicitly. |

A `Camera` or `Scene` you create yourself is used instead of the automatic ones.

### Scene

```python
scene = pb.Scene(camera=None, size=None, engine=None, samples=None, duration=None)
```

Arguments fall back to `pb.defaults`. `engine` is `"eevee"` or `"cycles"`
(`fast=False` / `cycles=True` are accepted too). `duration=4` sets a 4-second animation
(`frames=120` for a raw count).

| Method | Description |
|---|---|
| `render(filename, size, engine, gpu, samples, frame_rate, crf, frame=None, duration=None, frames=None, bake=False)` | `.png` still (or image sequence in `filename/` when it ends with `/`), `.mp4` animation encoded with ffmpeg. `frame` renders one frame, `bake` runs physics first. Returns the absolute path. |
| `duration`, `frames` | properties: length of the animation in seconds / in frames. |
| `set_animation_bounds(start, end)`, `set_frame(n)`, `set_gravity(...)` | |
| `set(**props)` | any property of the scene, its render, Eevee, Cycles or view settings: `scene.set(frame_step=2, film_transparent=True)` |
| `set_background(color, strength=1, image=None)` | world color or HDRI (lights the scene) |
| `set_color_management(view_transform="Filmic", look="None", exposure=0, gamma=1)` | |
| `set_eevee(ssr, refraction, gtao, motion_blur, soft_shadows, volumetric_tile_size, volumetric_samples)` | |
| `set_motion_blur(True, shutter)`, `set_transparent(True)`, `set_freestyle(line_thickness)` | |
| `add_bloom(intensity, radius, threshold)`, `add_volumetric_light(shadows)`, `add_glare(...)` | Eevee bloom, volumetrics, finishing glare stack |
| `use_gpu("CUDA")`, `set_denoising(True, denoiser=None)`, `bake()` | Cycles on GPU (CPU fallback); denoising (OptiX, else OpenImageDenoise, on by default for Cycles); bake physics over the animation range |
| `post` (alias `compositor`), `scene` | post-processing stack, the `bpy` scene |

### Camera

```python
pb.Camera(location=(0, 0, 0), target=None, rotation=(0, 0, 0), focus=None,
          aperture_fstop=2.8, aperture_ratio=1.0, aperture_blades=8, lens=50, clip=(0.1, 1000))
```

`target` is a point or an object to look at. `focus` enables depth of field on a point, an
object, or `True` for the target. Creating a camera makes it the active one.
`set_focus(target, fstop)`, `animate_lens`, `animate_fstop`, or simply `camera.to(lens=80, duration=1)`.

### Lights

| Class | Signature | Notes |
|---|---|---|
| `Sun` | `Sun(energy=5, color=None, rotation=None, target=None, location=(0, 0, 10), angle=0.5)` | Directional. 3–10 W/m² is daylight; `angle` softens shadows. |
| `PointLight` | `PointLight(location, energy=50, color=None, radius=0.1)` | Hundreds to thousands of W for a room. |
| `SpotLight` | `SpotLight(location, energy=50, color=None, rotation=None, target=None, angle=45, blend=0.15, radius=0.1)` | `angle` is the full cone in degrees. |
| `AreaLight` | `AreaLight(location, energy=100, color=None, rotation=None, target=None, size=(1, 1))` | A softbox. |

`light.to(energy=0, duration=2)` fades, `animate_energy` / `animate_color` for raw
keyframes, `light.set(shadow_soft_size=2)` for anything else.

### Meshes

Wherever `material` is expected, a color is accepted and wrapped in a `Material`.

| Class | Signature |
|---|---|
| `Cube` (alias `Box`) | `Cube(location, rotation, scale=(1, 1, 1), size=1, material=None, visible=True)` |
| `Plane` | `Plane(location, rotation, scale, size=1, material, visible)` |
| `Grid` | `Grid(location, rotation, scale, size=1, width=10, height=10, material, visible)` — subdivisions |
| `Sphere` (alias `UVSphere`) | `Sphere(location, rotation, scale, radius=1, segments=32, material, visible, smooth=True)` |
| `IcoSphere` | `IcoSphere(location, rotation, scale, radius=1, subdivisions=3, material, visible, smooth=True)` |
| `Circle` | `Circle(location, rotation, radius=1, segments=32, fill=False, material, visible)` |
| `Cylinder` | `Cylinder(location, rotation, scale, radius=1, depth=1, segments=32, caps="NGON", material, visible)` |
| `Cone`, `Torus` | `Cone(…, radius, depth, segments)`, `Torus(…, major_radius, minor_radius, div)` |
| `Line` | `Line(points, stroke_width=0.01, material, visible)` — polyline rendered as a tube |
| `Model` | `Model(path, location, rotation, scale, material, visible)` — `.glb` / `.gltf` / `.fbx` / `.obj`; the meshes are in `model.parts`, a rigged model keeps its `armature` and animation (`model.animation_range`) |
| `Empty` | `Empty(location, rotation, scale, name)` — invisible target or group |
| `merge(meshes)` | join several meshes into one object |

(`div=` is still accepted where `segments=` is documented.)

Mesh methods: `add_material(m)`, `set_material(m, index=0)`, `get_material(index_or_name)`
(wraps an existing material as a `NodeMaterial`, handy on imported models),
`material_names`, `set_smooth(True)` (alias `shade_smooth`), `subdivide(cuts)`,
`remove_faces("up")`, `convert_to_mesh()`, `apply_modifiers()`.

### Modifiers and physics

Every `add_*` returns the `bpy` modifier for further tweaking:

| Method | Description |
|---|---|
| `add_modifier(kind, **props)` | any Blender modifier by type (`"BEVEL"`, `"SOLIDIFY"`…) |
| `add_subdivision(levels, render_levels, smooth)` | subdivision surface |
| `add_displacement(texture, strength, midlevel, coordinates, direction)` | image path, `Image`, `Texture` or `Noise` as height map |
| `add_boolean(other, operation)`, `add_array(count, offset, relative, offset_object)`, `add_mirror(axis, mirror_object)` | |
| `add_wireframe(thickness)`, `add_bevel(width, segments)`, `add_solidify(thickness)`, `add_decimate(ratio)`, `add_remesh(mode, voxel_size)`, `add_smooth`, `add_ocean`, `add_wave`, `add_explode` | |
| `geometry(name)` | a Geometry Nodes modifier, see [Geometry nodes](#geometry-nodes) |
| `rigid_body(kind="ACTIVE", mass, friction, bounciness, shape, damping, kinematic)` | `"ACTIVE"` falls and collides, `"PASSIVE"` is a static obstacle |
| `throw(velocity, frame)` | initial velocity of a rigid body |
| `soft_body(mass, bend, push, pull)`, `cloth(quality, mass, stiffness)`, `collision()` | |

Physics is simulated over the animation range when rendering with `bake=True`.

### Tweens

Every object, group and node socket has a playhead. `to()` animates from the current
value to the given one with an easing, then advances the playhead, so calls chain into
a sequence:

```python
cube.to(location=(0, 0, 2), duration=1, easing="back-out")     # 0 s .. 1 s
cube.to(rotation=(0, 0, 180), scale=0.5, duration=0.5)         # 1 s .. 1.5 s
cube.wait(0.3).to(scale=0, duration=0.3, easing="back-in")     # 1.8 s .. 2.1 s
cube.to(location=(2, 0, 0), duration=0.5, start="<")           # in parallel with the previous tween
cube.to(location=(0, 0, 0), duration=0.5, start=3)             # at an absolute time
cube.to(scale=1, duration=pb.frames(12))                       # an exact number of frames

sphere.from_(scale=0, duration=0.5)                            # entrance: from 0 to the current scale
light.to(energy=0, duration=2)                                 # any property of the object or its data
camera.to(lens=80, duration=1)
mat.bsdf.roughness.to(1, duration=1)                           # a material socket
```

| Member | Description |
|---|---|
| `to(duration=0.6, easing="cubic-out", start=None, **props)` | tween to the given values |
| `from_(duration=0.6, easing="cubic-out", start=None, **props)` | tween from the given values to the current ones |
| `wait(seconds)` | advance the playhead |
| `cursor`, `cursor_frame` | the playhead in seconds (read / write) and in frames |
| `start` | `None`: the playhead; a time in seconds; `"<"`: the start of the previous tween |

`props` are `location`, `rotation` (degrees), `scale` (a number is broadcast), or any
animatable property of the object or its datablock (`energy`, `lens`, `hide_render`…).
Every frame gets a keyframe, so the easing is exact. Easing names are listed in
[Timeline and easings](#timeline-and-easings).

### Groups and motions

```python
cubes = pb.Group(pb.Cube(location=(i, 0, 0)) for i in range(20))
cubes.from_(scale=0, duration=0.4, stagger=0.05, easing="back-out")  # one after the other
cubes.to(location=lambda i, cube: (i, 0, math.sin(i)), duration=1)   # a value per member
cubes[5:].set_material("#FF0000")                                     # slicing, delegation
cubes.wait(0.7).pop_out(stagger=0.05, reverse=True)
```

A `Group` applies any method call to all its members (and returns the group), its tweens
accept `stagger` (seconds between members) and `reverse`, and a property given as a
callable receives `(index, member)`. The ready-made motions are group methods, each
starting at the group's playhead (or `start=`) and staggered:

| Method | Channel | Signature |
|---|---|---|
| `pop_in` | scale | `(duration=0.5, stagger=0.08, easing="back-out", start=None, scale_from=0, reverse=False)` |
| `pop_out` | scale | `(duration=0.5, stagger=0.08, easing="back-in", start=None, scale_to=0, reverse=False)` then hides |
| `slide_in` | location | `(offset=(0, -1, 0), duration=0.6, stagger=0.08, easing="cubic-out", start=None, reverse=False)` hidden before |
| `slide_out` | location | `(offset=(0, 1, 0), duration=0.6, stagger=0.08, easing="cubic-in", …)` then hides |
| `flip_in` | rotation | `(angle=(90, 0, 0), duration=0.6, stagger=0.08, easing="back-out", …)` hidden before |
| `flip_out` | rotation | `(angle=(-90, 0, 0), duration=0.6, stagger=0.08, easing="back-in", …)` then hides |
| `typewriter` | visibility | `(stagger=0.1, start=None, reverse=False)` |
| `wave` | location | `(duration=2, amplitude=0.2, period=1, phase=0.6, axis=1, start=None)` |
| `shake` | location | `(duration=1, amplitude=0.05, seed=0, start=None)` decaying jitter |

Offsets and angles are in the parent's local space: for an upright text, local Y is up,
so `slide_in(offset=(0, -1, 0))` rises from below. Motions on different channels combine;
two motions on the same channel of the same part overwrite each other where they overlap.
The same motions exist as functions in `pyblender.motion` (`motion.pop_in(title, ...)`).

### Materials and nodes

```python
pb.Material(color="#FFFFFF", roughness=0.5, metallic=0.5, specular=0.0, opacity=1.0,
            transmission=0.0, subsurface=0.0, emission_strength=0.0, emission_color=None,
            texture=None, normal=None, displacement=None, displacement_scale=1.0,
            cast_shadows=True, shadow_mode=None, blend_mode=None, **sockets)
```

A Principled BSDF. Numeric inputs also accept an image path, an `Image` or a node; any
other BSDF socket goes in `**sockets` (`clearcoat=0.5`, `sheen=0.2`, `ior=1.3`).
`opacity < 1` enables alpha blending, `transmission=1` makes glass, `emission_strength`
makes the surface glow (add `scene.add_bloom()` or `scene.post.glow()` for halos).

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
mat.bsdf.set(roughness=0.3, base_color="#FF8800")    # several at once
mat.bsdf.roughness.to(1, duration=1)                 # tween a socket
mat.bsdf.roughness.animate([0, 1], [0, 30])          # raw keyframes
noise.fac.map_range((0, 1), (0, 5)).clamp(0, 2)      # helpers on a socket
noise.fac.mix("#00FF00", fac=0.3)                    # MixRGB
noise.fac.apply("SINE")                              # any Math operation
```

Socket names are matched loosely: `base_color`, `"Base Color"` and `["Base Color"]` are
the same. Without an explicit socket, `>>` uses the first output and the first input.
`a.to(b)` with a node is the same as `a >> b`; `a.unlink()` removes incoming links.

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
`(location, rotation, strength, noise, flow, size, falloff)`, `animate_strength`, and
tweens (`wind.to(strength=0, duration=1)`).

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

A split text exposes its parts as a `Group` in `text.parts`
(`title.parts.pop_in(stagger=3)`); each part is a `TextObject` with `.body` and `.width`,
`text.width` is the total width. Tweens on the text itself move the whole group.

### Post-processing

`scene.post` (or `pb.post` for the default scene) is a stack of compositor effects
applied to the rendered image, in the order they are added. Each method returns an
`Effect` with named parameters:

```python
post = pb.post
post.vignette(0.4)
glow = post.glow(threshold=1.0, mix=0.2)
glow.set("mix", 0.4)
post.chromatic_aberration().animate("amount", [0, 0.5, 0], [40, 44, 50])   # raw frames
post.roll().burst("y", bursts=[(2, 2.3)], low=-200, high=200)              # seconds
post.glitch(bursts=[(1.3, 1.7), (3, 3.2)], strength=1.0, seed=0)
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
| `glitch(bursts, strength=1, seed=0)` | returns the effects | RGB split + slices + grain + flicker during each `(start, end)` in seconds. |

`Effect` methods: `set(name, value)`, `animate(name, values, frames)`,
`burst(name, bursts, low, high, seed=0, rest=0)` (bursts in seconds).

The compositor is also a node tree with the same idiom, for hand-built graphs:
`post.input` (Render Layers), `post.output` (Composite), `post.chain(node)` inserts a
node into the effect stack, and `create_glare`, `create_lens_distortion`,
`create_color_correction`, `create_sun_beams`, `create_blur`, `create_image`,
`create_texture`, `create_hue_saturation`, `create_translate`, `create_displace`,
`create_ellipse_mask`, `create_mix_rgb`, `create_math`… build nodes.

### Movies

Several scenes in one script, rendered one after the other and joined with crossfades:

```python
movie = pb.Movie("trailer.mp4", fade=0.5, size=(1280, 720), engine="cycles", samples=48,
                 audio="music.wav")

@movie.shot(duration=4)
def opening():
    pb.Text("hello", split="letters").parts.pop_in()
    pb.Camera((0, -8, 0), target=(0, 0, 0))

@movie.shot(duration=5, transition="cut", bake=True)
def cubes():
    pb.Group(pb.Cube(location=(i, 0, 0)) for i in range(5)).from_(scale=0, stagger=0.1)

movie.render()                      # or movie.render(only=["cubes"], force=False) while iterating
```

Blender is reset before each shot, so a shot builds its scene from scratch (automatic
camera and light when missing, `pb.scene()` / `pb.post` to tune it, or return a `Scene`).
`transition` is `"fade"` (the movie's `fade` seconds), `"cut"` or a number of seconds;
`movie.add_file("logo.mp4")` inserts an existing video; `audio` is a soundtrack cut to the
movie and faded out over `audio_fade` seconds. Shot videos are kept in
`<name>_shots/` next to the final file, and `pyblender.movie.join(paths, fades, filename)`
is the ffmpeg concatenation on its own.

### Timeline and easings

`pyblender.animation` is pure Python (no `bpy`), for value lists the tweens cannot express:

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
| `trailer.py` | mp4 | The pyblender trailer: ten shots in one `Movie` rendered with Cycles, a soundtrack generated with numpy, ~44 s. |
| `text_motion.py` | mp4 | Title card: group playheads, `pop_in`, `slide_in`, `wave`, exits. |
| `glitch_title.py` | mp4 | Sci-fi title with CRT look, chromatic aberration and glitch bursts. |
| `falling_cubes.py` | mp4 | Rigid bodies on a floor, `Group`, `bake=True`. |
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
for frame in (10, 60, 120):
    pb.render(f"preview_{frame}.png", size=(640, 360), samples=8, frame=frame)
```

**Sequence several objects.** Each object has its own playhead; to synchronise them,
pass explicit `start=` frames, or drive everything from one `Group`.

**Physics.** Give objects `rigid_body()`, a floor `rigid_body("PASSIVE")`, then
`pb.render("out.mp4", duration=4, bake=True)`.

**Imported model with its own materials.** `model = pb.Model("robot.glb")`, then
`model.get_material("Eyes").bsdf.emission_strength = 5`.

**Seamless loop.** Make every periodic motion complete a whole number of periods in the
duration and render that exact `duration` (or `frames=`).

**Anything pyblender does not expose.** `obj.set(**props)` reaches any property of the
object or its datablock, `scene.set(**props)` any render setting, `add_modifier(kind,
**props)` any modifier, `create(node_type, **props)` any node, and `cube.obj`,
`light.data`, `material.mat`, `scene.scene`, `post.tree`, `geo.group` are the raw `bpy`
objects.

## Migrating from the 2022 API

Most names were kept; the main changes:

| 2022 | Now |
|---|---|
| `mesh.modify_subdivide/displace/boolean/array/…()` | `mesh.add_subdivision/add_displacement/add_boolean/add_array/…()` |
| `mesh.modify_rigid_body()`, `modify_soft_body()`, `modify_collision()` | `mesh.rigid_body()`, `soft_body()`, `collision()` |
| `mesh.modify_geometry()` | `mesh.geometry()` |
| `mesh.scale(x, y, z)` | `mesh.resize((x, y, z))`; `scale` is now a property |
| hand-built value lists for every animation, in frames | `obj.to(...)`, `from_()`, `wait()`, groups with `stagger`, all in seconds |
| `scene.create_compositor()` | `scene.post` / `pb.post` (same `create_*` names, plus effects) |
| `node["Out"].to(other["In"])` | still works; `node.out >> other.in_` is shorter |
| `Particles(src, tgt, factor_random=…)` | `ParticleSystem(emitter, instance, velocity_random=…)`, see signature |
| `SpotLight(size=radians, focus_point=…)` | `SpotLight(angle=degrees, target=…)` (`focus_point` still accepted) |
| `Camera(focus_point=…)` for depth of field | `Camera(target=…, focus=True)` or `focus=(x, y, z)` |
| `Scene(cycles=True)`, `render(fast=False)` | still accepted; `engine="cycles"` is the documented form |
| `Scene.render(background_color=…, contrast=…)` | `scene.set_background()`, `scene.set_color_management()`, `scene.set_eevee()` |
| `Text(text, align="CENTER")` | `Text(body, align="center", split=…)`, upright by default |
| one script per scene, joined by hand | `pb.Movie` with one function per shot |
| `Image`, `Texture`, `Noise`, `RefractionBSDF`, `Box`, `UVSphere`, `shade_smooth` | unchanged |

Rotations were already in degrees and still are.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `ModuleNotFoundError: pyblender` | Use the `pyblender` command, or add the repository to `sys.path` before importing. |
| `Blender executable not found` | Set `BLENDER=/path/to/blender` or add it to `PATH`. |
| Black or empty render | With `pb.render` a camera and light are added; with your own `Scene`, add a `Sun(target=…)` and check the camera. |
| Particles invisible | The emitter was created with `visible=False`. Let `ParticleSystem(hide_emitter=True)` hide it. |
| Fog invisible in Eevee | Call `scene.add_volumetric_light()`. |
| Physics does nothing | Render with `bake=True` and set `duration=`. |
| `has no animatable property` | `to()` only knows transforms and properties of the object or its datablock; use `animate(attr, values, frames, data=…)` for anything else. |
| `cannot link nodes that belong to different node trees` | A node from one material was linked into another; create it in the target material. |
| Text appears flat / from above | `Text` is upright by default; put the camera on -Y. |
| `GPU rendering unavailable` warning | Cycles falls back to CPU. Check the driver, or pass `gpu=False`. |
| Eevee fails on a headless server | Eevee needs OpenGL. Use `engine="cycles"` or `xvfb-run`. |
