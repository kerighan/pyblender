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

    def create_object_info(self, mesh):
        node = self.nodes.new('GeometryNodeObjectInfo')
        node = GeoNode(node, self)
        node[0] = mesh.obj
        return node

    def create_random_value(self, data_type="FLOAT"):
        node = self.nodes.new('FunctionNodeRandomValue')
        node.data_type = data_type
        return GeoNode(node, self)
