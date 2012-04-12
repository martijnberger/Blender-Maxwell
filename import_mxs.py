import sys
import os
import time
import bpy
import mathutils

from mathutils import Matrix
from bpy_extras.io_utils import unpack_list, unpack_face_list
from bpy_extras.image_utils import load_image

from .pymaxwell import *


def load(operator, context, filepath):

    print('\nimporting mxs %r' % filepath)

    time_main = time.time()
    mxs_scene = Cmaxwell(mwcallback)

    ok = mxs_scene.readMXS(filepath)
    if ok == 0:
        print('\nError reading input file: %s' % (filepath))
        print(mxs_scene.getLastErrorString())

    time_new = time.time()
    time_old = time.time()
    print('\nDone parsing mxs %r in %.4f sec.' %
            (filepath, (time_new - time_main)))

    materials = {}
    mat_it = CmaxwellMaterialIterator()
    mat = mat_it.first(mxs_scene)
    while mat.isNull() == False:
        print("Material: %s" % mat.getName())
        materials[mat.getName()] = bpy.data.materials.new(mat.getName())
        mat = mat_it.next()

    it = CmaxwellObjectIterator()
    obj = it.first(mxs_scene)
    print(type(obj))
    n = 1
    imp = False
    ob_dict = {}
    while obj.isNull() == False:
        if(obj.isMesh() == 1):
            if(obj.getNumTriangles() > 0 or obj.getNumVertexes() > 0):
                try:
                    name = obj.getName()
                except UnicodeDecodeError:
                    obj.setName('corrupt' + str(n))
                    name = 'corrupt' + str(n)
                (base, pivot) = obj.getBaseAndPivot()
                triangles = obj.getNumTriangles()
                vertices = obj.getNumVertexes()
                normals = obj.getNumNormals()
                positions = obj.getNumPositionsPerVertex()
                verts = []
                faces = []
                i = 0
                num = triangles
                my_max = 0
                group_max = 0
                while i < num:
                    triangle = obj.getTriangle(i)
                    (v1, v2, v3, n1, n2, n3) = triangle
                    my_max = max(my_max, v1, v2, v3)
                    faces.append((v1, v2, v3))
                    i = i + 1
                i = 0
                while i <= my_max:
                    vert = obj.getVertex(i, 0)
                    verts.append((vert.x(), vert.z(), vert.y()))
                    i = i + 1
                for i in range(0, num):
                    print((obj.getNormal(n1,0), obj.getNormal(n1,0).x,
                                obj.getNormal(n1,0).z,obj.getNormal(n1,0).y)
                    #vec_n1 = mathutils.Vector

                me = bpy.data.meshes.new(str(n) + name)
                try:
                    me.materials.append(materials[obj.getMaterial().getName()])
                except KeyError:
                    print("KeyError")
                me.from_pydata(verts, [], faces)
                # edges or faces should be [], or you ask for problems
                me.update(calc_edges=True)    # Update mesh with new data
                ob = bpy.data.objects.new(name, me)
                ob.matrix_basis = (Matrix([(pivot.xAxis.x(), pivot.zAxis.x(),
                                            pivot.yAxis.x(), base.origin.x()),
                                  (-1 *pivot.xAxis.z(), -1 * pivot.zAxis.z(),
                                   -1 * pivot.yAxis.z(), -1 * base.origin.z()),
                                    (pivot.xAxis.y(),  pivot.zAxis.y(),
                                     pivot.yAxis.y(), base.origin.y()),
                                    (0.0, 0.0, 0.0, 1.0)]))

                ob_dict[name] = ob
                bpy.context.scene.objects.link(ob)

                me.update(calc_edges=True)
                n = n + 1
                imp=True
            else:
                print('NOT DONE:', obj.getName(), ' NULL: ', obj.isNull() )
                print('  ', obj.getNumVertexes(), '  ', obj.getNumTriangles())
        obj = it.next()
        #if imp:
        #    break
    time_new = time.time()
    print('imported %d objects in %.4f sec' % (n, (time_new - time_old)))
    time_old = time.time()

    it = CmaxwellObjectIterator()
    obj = it.first(mxs_scene)
    n = 1
    while obj.isNull() == False:
        if(obj.isInstance() == 1):
            (base,pivot) = obj.getBaseAndPivot()
            o = obj.getInstanced()
            parent_name = o.getName()
            ob = ob_dict[parent_name].copy()
            ob.matrix_basis = (Matrix([(pivot.xAxis.x(), pivot.zAxis.x(),
                                        pivot.yAxis.x(), base.origin.x()),
                            (-1 * pivot.xAxis.z(), -1 * pivot.zAxis.z(),
                             -1 * pivot.yAxis.z(), -1 * base.origin.z()),
                            (pivot.xAxis.y(), pivot.zAxis.y(),
                             pivot.yAxis.y(), base.origin.y()),
                          (0.0, 0.0, 0.0, 1.0)]))

            bpy.context.scene.objects.link(ob)
            n = n + 1

        obj = it.next()
    time_new = time.time()
    print('imported %d instance in %.4f sec' % (n, (time_new - time_old)))

    print(mxs_scene.getSceneInfo())

    print('finished importing: %r in %.4f sec.' %
            (filepath, (time_new - time_main)))
    return {'FINISHED'}
