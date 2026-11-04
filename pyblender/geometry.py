"""Geometry nodes: procedural geometry attached to a mesh as a modifier.

::

    geo = cube.geometry()                      # a Geometry Nodes modifier on the cube
    sphere = geo.create_icosphere(radius=0.1)
    points = geo.create_mesh_to_points()
    geo.input["Geometry"].to(points["Mesh"])
    instances = geo.create_instance_on_points()
    points["Points"].to(instances["Points"])
    sphere["Mesh"].to(instances["Instance"])
    instances["Instances"].to(geo.output["Geometry"])
"""

import bpy

from .nodes import NodeTree


class Geometry(NodeTree):
    """A geometry node group. ``input`` and ``output`` are the group's boundary nodes.

    Arguments:
        obj: the ``bpy`` object the modifier is added to (``mesh.geometry()`` does this).
    """

    def __init__(self, obj=None, name="geometry"):
        group = bpy.data.node_groups.new(name, "GeometryNodeTree")
        self.group = group
        self.nodes = group.nodes
        self.links = group.links

        group.inputs.new("NodeSocketGeometry", "Geometry")
        group.outputs.new("NodeSocketGeometry", "Geometry")
        self.input = self.create("NodeGroupInput")
        self.output = self.create("NodeGroupOutput")
        self.input["Geometry"].to(self.output["Geometry"])

        self.modifier = None
        if obj is not None:
            self.modifier = obj.modifiers.new(name, "NODES")
            self.modifier.node_group = group

    def _mesh(self, node_type, replace, output="Mesh", **properties):
        node = self.create(node_type, **properties)
        if replace:
            self.output.unlink("Geometry")
            node[output].to(self.output["Geometry"])
        return node

    # ------------------------------------------------------------------
    # Primitives (``replace=True`` makes the primitive the modifier's whole output)
    # ------------------------------------------------------------------

    def create_cube(self, size=(1, 1, 1), vertices=(2, 2, 2), replace=False):
        node = self._mesh("GeometryNodeMeshCube", replace)
        node["Size"] = size
        for name, count in zip(("Vertices X", "Vertices Y", "Vertices Z"), vertices):
            node[name] = count
        return node

    def create_icosphere(self, radius=1.0, subdivisions=1, replace=False):
        node = self._mesh("GeometryNodeMeshIcoSphere", replace)
        node["Radius"] = radius
        node["Subdivisions"] = subdivisions
        return node

    def create_uv_sphere(self, radius=1.0, segments=32, rings=16, replace=False):
        node = self._mesh("GeometryNodeMeshUVSphere", replace)
        node["Radius"] = radius
        node["Segments"] = segments
        node["Rings"] = rings
        return node

    def create_grid(self, size=(1, 1), vertices=(10, 10), replace=False):
        node = self._mesh("GeometryNodeMeshGrid", replace)
        node["Size X"], node["Size Y"] = size
        node["Vertices X"], node["Vertices Y"] = vertices
        return node

    def create_volume_cube(self, resolution=128, replace=False):
        node = self._mesh("GeometryNodeVolumeCube", replace, output="Volume")
        for name in ("Resolution X", "Resolution Y", "Resolution Z"):
            node[name] = resolution
        return node

    def create_curve_line(self, start=(0, 0, 0), end=(0, 0, 1)):
        node = self.create("GeometryNodeCurvePrimitiveLine")
        node["Start"] = start
        node["End"] = end
        return node

    def create_curve_circle(self, radius=1.0, resolution=32):
        node = self.create("GeometryNodeCurvePrimitiveCircle")
        node["Radius"] = radius
        node["Resolution"] = resolution
        return node

    # ------------------------------------------------------------------
    # Operations
    # ------------------------------------------------------------------

    def create_object_info(self, obj, transform_space="ORIGINAL", as_instance=False):
        """Bring another object's geometry in. ``transform_space``: ``ORIGINAL`` or ``RELATIVE``."""
        node = self.create("GeometryNodeObjectInfo", transform_space=transform_space)
        node.node.inputs["Object"].default_value = obj.obj
        node["As Instance"] = as_instance
        return node

    def create_instance_on_points(self, scale=(1, 1, 1)):
        node = self.create("GeometryNodeInstanceOnPoints")
        node["Scale"] = scale
        return node

    def create_mesh_to_points(self, mode="VERTICES", radius=0.05):
        node = self.create("GeometryNodeMeshToPoints", mode=mode)
        node["Radius"] = radius
        return node

    def create_distribute_points(self, density=10.0, seed=0, mode="RANDOM"):
        node = self.create("GeometryNodeDistributePointsOnFaces", distribute_method=mode)
        if mode == "RANDOM":
            node["Density"] = density
        node["Seed"] = seed
        return node

    def create_realize_instances(self):
        return self.create("GeometryNodeRealizeInstances")

    def create_join_geometry(self):
        return self.create("GeometryNodeJoinGeometry")

    def create_transform(self, translation=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)):
        node = self.create("GeometryNodeTransform")
        node["Translation"] = translation
        node["Rotation"] = rotation
        node["Scale"] = scale
        return node

    def create_set_material(self, material):
        node = self.create("GeometryNodeSetMaterial")
        node.node.inputs["Material"].default_value = material.mat
        return node

    def create_set_position(self):
        return self.create("GeometryNodeSetPosition")

    def create_position(self):
        return self.create("GeometryNodeInputPosition")

    def create_normal(self):
        return self.create("GeometryNodeInputNormal")

    def create_index(self):
        return self.create("GeometryNodeInputIndex")

    def create_volume_to_mesh(self, resolution_mode="GRID", threshold=0.1):
        node = self.create("GeometryNodeVolumeToMesh", resolution_mode=resolution_mode)
        node["Threshold"] = threshold
        return node

    def create_mesh_boolean(self, operation="DIFFERENCE"):
        return self.create("GeometryNodeMeshBoolean", operation=operation)

    def create_subdivision_surface(self, level=1):
        node = self.create("GeometryNodeSubdivisionSurface")
        node["Level"] = level
        return node

    def create_curve_to_points(self, count=30, mode="COUNT"):
        node = self.create("GeometryNodeCurveToPoints", mode=mode)
        if mode == "COUNT":
            node["Count"] = count
        return node

    def create_curve_to_mesh(self):
        return self.create("GeometryNodeCurveToMesh")

    def create_mesh_to_curve(self):
        return self.create("GeometryNodeMeshToCurve")

    def create_random_value(self, data_type="FLOAT", minimum=0.0, maximum=1.0, seed=0):
        node = self.create("FunctionNodeRandomValue", data_type=data_type)
        index = {"FLOAT": (2, 3), "FLOAT_VECTOR": (0, 1), "INT": (4, 5)}.get(data_type)
        if index is not None:
            node.node.inputs[index[0]].default_value = minimum
            node.node.inputs[index[1]].default_value = maximum
        node["Seed"] = seed
        return node

    def create_rotate_vector(self, rotation_type="AXIS_ANGLE"):
        return self.create("ShaderNodeVectorRotate", rotation_type=rotation_type)

    def create_scene_time(self):
        return self.create("GeometryNodeInputSceneTime")
