import bpy
import sys
import os
import time
import math

from mathutils import Matrix, Vector
from bpy_extras.io_utils import unpack_list, unpack_face_list
from bpy_extras.image_utils import load_image

from .pymaxwell import *

pi = math.pi

def CbasePivot2Matrix(b,p):
    bscale = b.xAxis.x()
    if bscale == 0:
        bscale = 1
    x = p.xAxis * bscale
    y = p.yAxis * bscale
    z = p.zAxis * bscale
    return Matrix([(x.x(),      z.x(),      y.x(),      b.origin.x()),
                   (-1 * x.z(), -1 * z.z(), -1 * y.z(), -1 * b.origin.z()),
                   (x.y(),      z.y(),      y.y(),       b.origin.y()),
                   (0.0,        0.0,        0.0,        1.0)])


def Cbase2Matrix(b):
    m = Matrix()
    m.col[0] = Cvector2Vector(b.xAxis).to_4d()
    m.col[1] = Cvector2Vector(b.zAxis).to_4d()
    m.col[2] = Cvector2Vector(b.yAxis).to_4d()
    return m

def Cvector2Vector(v):
  return Vector((v.x(), -1.0 * v.z(), v.y()))

def write_camera(context, camera):
  origin, focalPoint, up, focalLength, fStop, stepTime = camera.getStep(0)
  camValues = camera.getValues()
  print(camera.getName())
  dir_vect = Cvector2Vector(origin) - Cvector2Vector(focalPoint)
  q = dir_vect.normalized().rotation_difference((0,0,-1))
  qe = q.to_euler()
  obj = bpy.ops.object.add(type='CAMERA',
                     location=Cvector2Vector(origin),
                     rotation=(qe.x, qe.y, qe.z))
  ob = bpy.context.object
  up2 = (ob.matrix_world.col[3].normalized() + ob.matrix_world.col[1].normalized()).normalized().to_3d()
  axis = dir_vect
  angle = up2.angle(Cvector2Vector(up))
  axis = (axis[0], axis[1], axis[2])
  print(angle, axis) 
  bpy.ops.transform.rotate(value=(angle,),axis=axis)
  ob.name = camera.getName()
  cam = ob.data
  cam.lens = focalLength * 1000 # Maxwell lens is in meters
  # Cycles
  cam.cycles.aperture_fstop = fStop
  # Luxrender
  #cam.luxrender_camera.fstop = fStop
  cam.name = camera.getName()

  return

def load(operator, context, filepath):
    '''load a maxwell file'''

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

    for cam_name in mxs_scene.getCameraNames():
      write_camera(context, mxs_scene.getCamera(cam_name))

    materials = {}
    mat_it = CmaxwellMaterialIterator()
    mat = mat_it.first(mxs_scene)
    while mat.isNull() == False:
        print("Material: %s" % mat.getName())
        materials[mat.getName()] = bpy.data.materials.new(mat.getName())
        mat = mat_it.next()

    it = CmaxwellObjectIterator()
    obj = it.first(mxs_scene)
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
                normal_count = obj.getNumNormals()
                positions = obj.getNumPositionsPerVertex()
                verts = []
                faces = []
                normals = []
                vert_norm = {}
                i = 0
                num = triangles
                max_vertex = 0
                max_normal = 0
                group_max = 0
                for i in range(triangles):
                    triangle = obj.getTriangle(i)
                    (v1, v2, v3, n1, n2, n3) = triangle
                    max_vertex = max(max_vertex, v1, v2, v3)
                    max_normal = max(max_normal, n1, n2, n3)
                    faces.append((v1, v2, v3))
                    vert_norm[v1] = n1
                    vert_norm[v2] = n2
                    vert_norm[v3] = n3
                for i in range(max_vertex + 1):
                    vert = obj.getVertex(i, 0)
                    verts.append((vert.x(), vert.z(), vert.y()))
                for i in range(max_vertex + 1):
                    n = obj.getNormal(vert_norm[i],0)
                    normals.append((n.x(), n.z(), n.y())) 

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
 
                print("{} verts: {}\tfaces: {}\tnormals: {}".format(name, len(verts), len(faces), len(normals)))

                me.vertices.foreach_set("co", unpack_list(verts))
                me.vertices.foreach_set("normal",  unpack_list(normals))
                me.tessfaces.foreach_set("vertices_raw", unpack_face_list(faces))
                me.update(calc_edges=True)    # Update mesh with new data
                me.validate()

                ob = bpy.data.objects.new(name, me)
#                ob.matrix_basis = (Matrix([(pivot.xAxis.x(), pivot.zAxis.x(),
#                                   pivot.yAxis.x(), base.origin.x()),
#                                    (-1 * pivot.xAxis.z(), -1 * pivot.zAxis.z(),
#                                   -1 * pivot.yAxis.z(), -1 * base.origin.z()),
#                                    (pivot.xAxis.y(),  pivot.zAxis.y(),
#                                     pivot.yAxis.y(), base.origin.y()),
#                                    (0.0, 0.0, 0.0, 1.0)]))
#                print(ob.matrix_basis)
#                print(CbasePivot2Matrix(base,pivot))
                ob.matrix_basis = CbasePivot2Matrix(base,pivot)
                ob_dict[name] = ob
                if len(verts) > 5000:
                    ob.draw_type = 'BOUNDS'
                bpy.context.scene.objects.link(ob)
                me.update(calc_edges=True)
                #return {'FINISHED'}
            else:
                pass
                #print('NOT DONE:', obj.getName(), ' NULL: ', obj.isNull())
                #print('  ', obj.getNumVertexes(), '  ', obj.getNumTriangles())
        obj = it.next()

    time_new = time.time()
    print('imported %d objects in %.4f sec' % (len(ob_dict), (time_new - time_old)))
    time_old = time.time()

    it = CmaxwellObjectIterator()
    obj = it.first(mxs_scene)
    instance_count = 0
    while obj.isNull() == False:
        if(obj.isInstance() == 1):
            (base, pivot) = obj.getBaseAndPivot()
            o = obj.getInstanced()
            parent_name = o.getName()
            ob = ob_dict[parent_name].copy()
            ob.matrix_basis = CbasePivot2Matrix(base,pivot)
            if len(ob.data.vertices) > 5000:
                ob.draw_type = 'BOUNDS'
            mat = obj.getMaterial()
            s = ob.material_slots
            if mat.isNull() == False:
              if not mat.getName() == ob.material_slots[0].name:
                print( mat.getName(), " ", ob.material_slots[0].name)
                ob.material_slots[0].link = 'OBJECT'
                ob.material_slots[0].material = materials[mat.getName()]
            ob.matrix_basis = (Matrix([(pivot.xAxis.x(), pivot.zAxis.x(),
                                        pivot.yAxis.x(), base.origin.x()),
                            (-1 * pivot.xAxis.z(), -1 * pivot.zAxis.z(),
                             -1 * pivot.yAxis.z(), -1 * base.origin.z()),
                            (pivot.xAxis.y(), pivot.zAxis.y(),
                             pivot.yAxis.y(), base.origin.y()),
                          (0.0, 0.0, 0.0, 1.0)]))
            bpy.context.scene.objects.link(ob)
            instance_count += 1
        obj = it.next()

    time_new = time.time()
    print('imported %d instance in %.4f sec' % (instance_count, (time_new - time_old)))

    print(mxs_scene.getSceneInfo()," Triangle groups: ",mxs_scene.getTriangleGroupsCount())

    print('finished importing: %r in %.4f sec.' %
            (filepath, (time_new - time_main)))
    return {'FINISHED'}
