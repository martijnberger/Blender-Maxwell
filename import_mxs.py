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
                    if(n1 + n2 + n3 < 1):
                        continue
                    if(n1 == n2 == n3):
                        vec_n = mathutils.Vector((obj.getNormal(n1, 0).x(),
                                                  obj.getNormal(n1, 0).z(),
                                                  obj.getNormal(n1, 0).y())).normalized()
                    else:
                        vec_n1 = mathutils.Vector((obj.getNormal(n1, 0).x(),
                                                   obj.getNormal(n1, 0).z(),
                                                   obj.getNormal(n1, 0).y())).normalized()
                        vec_n2 = mathutils.Vector((obj.getNormal(n2, 0).x(),
                                                   obj.getNormal(n2, 0).z(),
                                                   obj.getNormal(n2, 0).y())).normalized()
                        vec_n3 = mathutils.Vector((obj.getNormal(n3, 0).x(),
                                                   obj.getNormal(n3, 0).z(),
                                                   obj.getNormal(n3, 0).y())).normalized()
                        vec_n = (vec_n1 + vec_n2 + vec_n3) / 3
                    
                    (v1, v2, v3) = faces[i]
                    vec_u = mathutils.Vector((verts[v2][0] - verts[v1][0],
                                              verts[v2][1] - verts[v1][1],
                                              verts[v2][2] - verts[v1][2]))
                    vec_v = mathutils.Vector((verts[v3][0] - verts[v1][0],
                                              verts[v3][1] - verts[v1][1],
                                              verts[v3][2] - verts[v1][2]))
#                   vec_cross = vec_e1.cross(vec_e2).normalized()
                    vec_cross = mathutils.Vector(((vec_u.y * vec_v.z) - (vec_u.z * vec_v.y),
                                                  (vec_u.z * vec_v.x) - (vec_u.x * vec_v.z),
                                                  (vec_u.x * vec_v.y) - (vec_u.y * vec_v.x))).normalized()
                    dot = vec_n.dot(vec_cross.normalized())
                    #print("dot:", vec_n.dot(vec_cross.normalized()))
                    print( round(dot,2))
                    if( round(dot,2) < 0):
#                        print("face normal: ", vec_n)
#                        print("plane vect", vec_cross)
                        print("CHANGING VERTEX ORDER", round(dot,2))
#                        faces[i] = (v3, v2, v1)
#                    if(abs(round(dot,2)) < 0.95):
#                        print("smooth_face")

                print(str(n) + name)
                me = bpy.data.meshes.new(str(n) + name)
                mat_name = obj.getMaterial().getName()
                if mat_name != "None":
                    try:
                        me.materials.append(materials[obj.getMaterial().getName()])
                    except KeyError:
                        print("Cant Find Material", mat_name)
                #me.from_pydata(verts, [], faces)
                me.vertices.add(len(verts))
                me.tessfaces.add(len(faces))
                
                print(name ," verts: ", len(unpack_list(verts))/3 ," ", len(verts))
                me.vertices.foreach_set("co", unpack_list(verts))
                print(name, " faces: ", len(unpack_face_list(faces))/4, " ", len(faces))
                me.tessfaces.foreach_set("vertices_raw", unpack_face_list(faces))
                me.update()
                me.validate()

                # edges or faces should be [], or you ask for problems
                me.update(calc_edges=True)    # Update mesh with new data
                ob = bpy.data.objects.new(name, me)
                ob.matrix_basis = (Matrix([(pivot.xAxis.x(), pivot.zAxis.x(),
                                            pivot.yAxis.x(), base.origin.x()),
                                  (-1 * pivot.xAxis.z(), -1 * pivot.zAxis.z(),
                                   -1 * pivot.yAxis.z(), -1 * base.origin.z()),
                                    (pivot.xAxis.y(),  pivot.zAxis.y(),
                                     pivot.yAxis.y(), base.origin.y()),
                                    (0.0, 0.0, 0.0, 1.0)]))

                for i in range(0, num):
                    vec_n1 = mathutils.Vector((obj.getNormal(n1, 0).x(),
                                               obj.getNormal(n1, 0).z(),
                                               obj.getNormal(n1, 0).y()))
                    vec_n2 = mathutils.Vector((obj.getNormal(n2, 0).x(),
                                               obj.getNormal(n2, 0).z(),
                                               obj.getNormal(n2, 0).y()))
                    vec_n3 = mathutils.Vector((obj.getNormal(n3, 0).x(),
                                               obj.getNormal(n3, 0).z(),
                                               obj.getNormal(n3, 0).y()))
                    vec_n = (vec_n1 + vec_n2 + vec_n3) / 3
                    (v1, v2, v3) = faces[i]
                    vec_e1 = mathutils.Vector((verts[v2][0] - verts[v1][0],
                                               verts[v2][1] - verts[v1][1],
                                               verts[v2][2] - verts[v1][2]))
                    vec_e2 = mathutils.Vector((verts[v3][0] - verts[v2][0],
                                               verts[v3][1] - verts[v2][1],
                                               verts[v3][2] - verts[v2][2]))
                    vec_cross = vec_e1.cross(vec_e2)
                    dot = vec_n.dot(vec_cross.normalized())
                    #print("dot:", vec_n.dot(vec_cross.normalized()))
                    if(dot < 0.95 or dot > 1.05):
                        #print("CHANGING VERTEX ORDER")
                        faces[i] = (v1, v3, v2)

                print(str(n) + name)
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
                                  (-1 * pivot.xAxis.z(), -1 * pivot.zAxis.z(),
                                   -1 * pivot.yAxis.z(), -1 * base.origin.z()),
                                    (pivot.xAxis.y(),  pivot.zAxis.y(),
                                     pivot.yAxis.y(), base.origin.y()),
                                    (0.0, 0.0, 0.0, 1.0)]))

                ob_dict[name] = ob
                bpy.context.scene.objects.link(ob)

                me.update(calc_edges=True)
                n = n + 1
                imp = True
            else:
                print('NOT DONE:', obj.getName(), ' NULL: ', obj.isNull())
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
            (base, pivot) = obj.getBaseAndPivot()
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

    print(mxs_scene.getSceneInfo()," Triangle groups: ",mxs_scene.getTriangleGroupsCount())

    print('finished importing: %r in %.4f sec.' %
            (filepath, (time_new - time_main)))
    return {'FINISHED'}
