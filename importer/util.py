__author__ = 'Martijn Berger'
__license__ = "GPL"

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

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