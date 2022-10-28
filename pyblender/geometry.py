import bpy

from pyblender.utils import random_string


class GeoNode:
    def __init__(self, node, group):
        self._node = node
        self._group = group
        self._current = None

    def __setitem__(self, key, value):
        self._node.inputs[key].default_value = value

    def __getitem__(self, key):
        self._current = key
        return self

    def to(self, target):
        self._group.link(self, target, self._current, target._current)
        target._current = None
        self._current = None

    def animate(self, key, values, frames=None):
        path = self._node.inputs[key]
        frames = range(len(values)) if frames is None else frames
        for frame, value in zip(frames, values):
            path.default_value = value
            path.keyframe_insert(data_path="default_value", frame=frame)

    def animate_value(self, values, frames=None):
        path = self._node.outputs["Value"]
        frames = range(len(values)) if frames is None else frames
        for frame, value in zip(frames, values):
            path.default_value = value
            path.keyframe_insert(data_path="default_value", frame=frame)


class Geometry:
    def __init__(self, obj=None):
        node_group = bpy.data.node_groups.new('GeometryNodes',
                                              'GeometryNodeTree')

        out_node = node_group.nodes.new('NodeGroupOutput')
        out_node.inputs.new('NodeSocketGeometry', 'Geometry')

        in_node = node_group.nodes.new('NodeGroupInput')
        in_node.outputs.new('NodeSocketGeometry', 'Geometry')

        node_group.links.new(in_node.outputs['Geometry'],
                             out_node.inputs['Geometry'])

        self.out_node = GeoNode(out_node, self)
        self.in_node = GeoNode(in_node, self)
        self.links = node_group.links
        self.nodes = node_group.nodes

        if obj is not None:
            obj.modifiers.new(random_string(10), "NODES")
            obj.modifiers[-1].node_group = node_group

    def link(self, source, target, out, inp):
        source = self.get_node(source)
        target = self.get_node(target)
        self.links.new(source.outputs[out], target.inputs[inp])

    def get_node(self, name):
        if isinstance(name, str):
            name = self.nodes.get(name)
        elif hasattr(name, "_node"):
            name = name._node
        return name

    def create_cube(self, size=(1, 1, 1), vertices=(2, 2, 2), replace=True):
        node = self.nodes.new('GeometryNodeMeshCube')
        node.inputs[0].default_value = size
        for i in range(1, 4):
            node.inputs[i].default_value = vertices[i - 1]
        mesh_node = GeoNode(node, self)
        if replace:
            mesh_node["Mesh"].to(self.out_node["Geometry"])
        return mesh_node

    def create_volume_cube(self, resolution=128, replace=True):
        node = self.nodes.new('GeometryNodeVolumeCube')
        mesh_node = GeoNode(node, self)
        if replace:
            mesh_node["Volume"].to(self.out_node["Geometry"])
        mesh_node["Resolution X"] = resolution
        mesh_node["Resolution Y"] = resolution
        mesh_node["Resolution Z"] = resolution
        return mesh_node

    def create_volume_to_mesh(self, resolution_mode="GRID"):
        node = self.nodes.new('GeometryNodeVolumeToMesh')
        node.resolution_mode = resolution_mode
        mesh_node = GeoNode(node, self)
        return mesh_node

    def create_icosphere(self, replace=True):
        node = self.nodes.new('GeometryNodeMeshIcoSphere')
        mesh_node = GeoNode(node, self)
        if replace:
            mesh_node["Mesh"].to(self.out_node["Geometry"])
        return mesh_node

    def create_instance_on_points(self, scale=(1, 1, 1)):
        node = self.nodes.new('GeometryNodeInstanceOnPoints')
        node = GeoNode(node, self)
        node["Scale"] = scale
        return node

    def create_object_info(self, mesh, transform_space="ORIGINAL"):
        node = self.nodes.new('GeometryNodeObjectInfo')
        node.transform_space = transform_space
        node = GeoNode(node, self)
        node[0] = mesh.obj
        return node
    
    def create_join_geometry(self):
        node = self.nodes.new('GeometryNodeJoinGeometry')
        node = GeoNode(node, self)
        return node

    def create_transform(self):
        node = self.nodes.new('GeometryNodeTransform')
        node = GeoNode(node, self)
        return node

    def create_set_material(self, material):
        node = self.nodes.new('GeometryNodeSetMaterial')
        node = GeoNode(node, self)
        node[2] = material.mat
        return node
    
    def create_position(self):
        node = self.nodes.new('GeometryNodeInputPosition')
        node = GeoNode(node, self)
        return node

    def create_set_position(self):
        node = self.nodes.new('GeometryNodeSetPosition')
        node = GeoNode(node, self)
        return node

    def create_normal(self):
        node = self.nodes.new("GeometryNodeInputNormal")
        node = GeoNode(node, self)
        return node
    
    def create_clamp(self, min_val=0, max_val=1):
        node = self.nodes.new("ShaderNodeClamp")
        node = GeoNode(node, self)
        node[1] = min_val
        node[2] = max_val
        return node
        
    def create_operation(self, operation="MULTIPLY", value=5):
        if operation == "SCALE":
            node = self.nodes.new("ShaderNodeVectorMath")
            node.operation = operation
            node.inputs[3].default_value = value
        else:
            node = self.nodes.new("ShaderNodeMath")
            node.operation = operation
            node.inputs[1].default_value = value
        return GeoNode(node, self)
    
    def create_rotate_vector(self):
        node = self.nodes.new("ShaderNodeVectorRotate")
        return GeoNode(node, self)

    def create_separate_xyz(self):
        node = self.nodes.new("ShaderNodeSeparateXYZ")
        return GeoNode(node, self)

    def create_combine_xyz(self):
        node = self.nodes.new("ShaderNodeCombineXYZ")
        return GeoNode(node, self)

    def create_instance_on_points(self):
        node = self.nodes.new('GeometryNodeInstanceOnPoints')
        node = GeoNode(node, self)
        return node

    def create_curve_to_points(self, count=30):
        node = self.nodes.new('GeometryNodeCurveToPoints')
        node = GeoNode(node, self)
        node["Count"] = count
        return node

    def create_mesh_boolean(self):
        node = self.nodes.new('GeometryNodeMeshBoolean')
        node = GeoNode(node, self)
        return node

    def create_curve_to_mesh(self):
        node = self.nodes.new('GeometryNodeCurveToMesh')
        node = GeoNode(node, self)
        return node

    def create_mesh_to_curve(self):
        node = self.nodes.new('GeometryNodeMeshToCurve')
        node = GeoNode(node, self)
        return node

    def create_curve_line(self):
        node = self.nodes.new('GeometryNodeCurvePrimitiveLine')
        node = GeoNode(node, self)
        return node

    def create_random_value(self, data_type="FLOAT"):
        node = self.nodes.new('FunctionNodeRandomValue')
        node.data_type = data_type
        return GeoNode(node, self)

    def create_vector_math(self, operation="SCALE", value=None):
        node = self.nodes.new('ShaderNodeVectorMath')
        node.operation = operation
        node = GeoNode(node, self)
        if value is not None:
            node[1] = value
        return node

    def create_value(self, value=.5):
        node = self.nodes.new("ShaderNodeValue")
        node.outputs["Value"].default_value = value
        return GeoNode(node, self)
