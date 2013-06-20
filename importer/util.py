__author__ = 'mberger'

from mathutils import Matrix, Vector
from bpy_extras.io_utils import axis_conversion

AxisMatrix3  = axis_conversion(from_forward='-Z', from_up='Y', to_forward='Y', to_up='Z')

AxisMatrix = AxisMatrix3.to_4x4()

def CbasePivot2Matrix(b,p):
    """Broken for some reason)"""
    return  AxisMatrix * Cbase2Matrix4(b) * Cbase2Matrix4(p)


def Cbase2Matrix3(b):
    x = b.x
    z = b.z
    y = b.y
    return Matrix([(x.x, y.x, z.x),
                   (x.y, y.y, z.y),
                   (x.z, y.z, z.z)])

def Cbase2Matrix4(b):
    x = b.x
    y = b.y
    z = b.z
    o = b.origin
    return Matrix([(x.x, y.x, z.x, o.x),
                   (x.y, y.y, z.y, o.y),
                   (x.z, y.z, z.z, o.z),
                   (0,   0,   0,   1)])

def Cvector2Vector(v):
    return Vector((v.x, v.y, v.z))