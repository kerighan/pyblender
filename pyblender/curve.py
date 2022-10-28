import bpy
from pyblender.mesh import Mesh
from pyblender.utils import to_radians


class Circle(Mesh):
    def __init__(
        self,
        location=(0, 0, 0),
        rotation=(0, 0, 0),
        radius=1
    ):
        rotation = to_radians(rotation)
        bpy.ops.curve.primitive_bezier_circle_add(
            radius=radius, location=location, rotation=rotation)
        self.obj = bpy.context.scene.objects[-1]


class Bezier(Mesh):
    def __init__(
        self,
        coords
    ):
        # create the Curve Datablock
        curveData = bpy.data.curves.new('myCurve', type='CURVE')
        curveData.dimensions = '3D'
        curveData.resolution_u = 1

        # map coords to spline
        polyline = curveData.splines.new('NURBS')
        polyline.points.add(len(coords))
        for i, coord in enumerate(coords):
            x,y,z = coord
            polyline.points[i].co = (x, y, z, 1)

        # create Object
        obj = bpy.data.objects.new('myCurve', curveData)

        # attach to scene and validate context
        bpy.context.collection.objects.link(obj)
        self.obj = obj
        self.deselect_all()
        self.select()
