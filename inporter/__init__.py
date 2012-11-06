import bpy
import os
import time
import math

from mathutils import Matrix, Vector
from bpy_extras.io_utils import unpack_list, unpack_face_list
from bpy_extras.image_utils import load_image
from collections import OrderedDict

from ..pymaxwell import *

from ..outputs import MaxwellLog

pi = math.pi

def CbasePivot2Matrix(b,p):
  '''Calculate a transformation matrix based on a MXS base and pivot'''
  bscale = b.xAxis.x() #TODO we should build a matrix out of whole base and pivot
  if bscale == 0: # some items are scaled by base rather then by pivot
    bscale = 1
  x = p.xAxis * bscale
  y = p.yAxis * bscale
  z = p.zAxis * bscale
  return Matrix([(x.x(),      z.x(),      y.x(),      b.origin.x()),
                 (-1 * x.z(), -1 * z.z(), -1 * y.z(), -1 * b.origin.z()),
                 (x.y(),      z.y(),      y.y(),       b.origin.y()),
                 (0.0,        0.0,        0.0,        1.0)])


def Cbase2Matrix(b):
  x = b.xAxis
  z = b.zAxis
  y = b.yAxis
  return Matrix([(x.x(),      x.y(),      x.z(),      b.origin.x()),
                 (y.x(),      y.y(),      y.z(),       b.origin.y()),
                 (z.x(),      z.y(),      z.z(),       b.origin.z()),
                 (0.0,        0.0,        0.0,        1.0)])


def Cvector2Vector(v):
  return Vector((v.x(), -1.0 * v.z(), v.y()))


def write_camera(context, camera):
  origin, focalPoint, up, focalLength, fStop, stepTime = camera.getStep(0)
  camValues = camera.getValues()
  MaxwellLog(camera.getName())
  dir_vect = Cvector2Vector(origin) - Cvector2Vector(focalPoint)
  q = dir_vect.normalized().rotation_difference((0,0,-1))
  qe = q.to_euler()
  obj = bpy.ops.object.add(type='CAMERA',
                     location=Cvector2Vector(origin),
                     rotation=(qe.x, qe.y, qe.z))
  ob = bpy.context.object
  up2 = ob.matrix_world.col[1].to_3d()
  dir = ob.matrix_world.col[3] - ob.matrix_world.col[2]
  rot_diff = up2.rotation_difference(Cvector2Vector(up))
  ob.rotation_euler.rotate(rot_diff)
  ob.name = camera.getName()
  cam = ob.data
  cam.lens = focalLength * 1000 # Maxwell lens is in meters
  cam.sensor_height = camValues['filmHeight'] * 1000.0
  cam.sensor_width = camValues['filmWidth'] * 1000.0
  shift_x, shift_y = camera.getShiftLens()
  cam.shift_x = shift_x / 100.0
  cam.shift_y = shift_y / -100.0
  # Cycles
  cam.cycles.aperture_fstop = fStop
  # Luxrender
  #cam.luxrender_camera.fstop = fStop
  cam.name = camera.getName()


def write_mesh(context, obj, materials):
  n = 0
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
    uv_layer_count = obj.getNumChannelsUVW()
    verts = []
    faces = []
    normals = []
    vert_norm = {}
    mats = {}
    mat_index = []
    uvs = []
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
        mat = obj.getTriangleMaterial(i)
        if not mat.isNull():
          mat_name = mat.getName()
          if not mat_name in mats:
            mats[mat_name] = len(mats)
          mat_index.append(mats[mat_name])
        else:
          mat_index.append(0)
        faces.append((v1, v2, v3))
        vert_norm[v1] = n1
        vert_norm[v2] = n2
        vert_norm[v3] = n3
        if uv_layer_count > 0:
          u1, v1, w1, u2, v2, w2, u3, v3, w3 = obj.getTriangleUVW(i, 0)
          uvs.append(( u1, v1, u2, v2, u3, v3, 0.0, 0.0 ))
    for i in range(max_vertex + 1):
        vert = obj.getVertex(i, 0)
        verts.append((vert.x(), vert.z(), vert.y()))
    for i in range(max_vertex + 1):
        n = obj.getNormal(vert_norm[i],0)
        normals.append((n.x(), n.z(), n.y()))

    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.tessfaces.add(len(faces))
    if len(mats) >= 1:
        mats_sorted = OrderedDict(sorted(mats.items(), key=lambda x: x[1]))
        for k in mats_sorted.keys():
            me.materials.append(materials[k])
#            print("setting {}".format(mat_name, k ))
    else:
        MaxwellLog("WARNING OBJECT {} HAS NO MATERIAL".format(obj.getName()))

    #print("{} verts: {}\tfaces: {}\tnormals: {}".format(name, len(verts), len(faces), len(normals)))

    me.vertices.foreach_set("co", unpack_list(verts))
    me.vertices.foreach_set("normal",  unpack_list(normals))
    me.tessfaces.foreach_set("vertices_raw", unpack_face_list(faces))
    me.tessfaces.foreach_set("material_index", mat_index) 
    if len(uvs) > 0:
        me.tessface_uv_textures.new()
        for i in range(len(uvs)):
            me.tessface_uv_textures[0].data[i].uv_raw = uvs[i]

    me.update(calc_edges=True)    # Update mesh with new data
    me.validate()

    ob = bpy.data.objects.new(name, me)
    ob.matrix_basis = CbasePivot2Matrix(base,pivot)
    if len(verts) > 5000:
        ob.draw_type = 'BOUNDS'
    bpy.context.scene.objects.link(ob)
    me.update(calc_edges=True)
    return (name, ob)
  else:
      MaxwellLog('NOT DONE:', obj.getName(), ' NULL: ', obj.isNull())
      MaxwellLog('  ', obj.getNumVertexes(), '  ', obj.getNumTriangles())
  return (False, False) 



def write_materials(context, mxs_scene, basepath):
    materials = {}
    mat_it = CmaxwellMaterialIterator()
    mat = mat_it.first(mxs_scene)
    while mat.isNull() == False:
        #MaxwellLog("Material: %s" % mat.getName())
        bmat = bpy.data.materials.new(mat.getName())
        r, g, b = 0.0, 0.0, 0.0
        textures = {}
        if mat.getNumLayers() > 0:
            layer = mat.getLayer(0)
            if layer.getNumBSDFs() > 0:
                bsdf = layer.getBSDF(0)
                refl = bsdf.getReflectance()
                color = refl.getColor('color')
                r, g, b = color.rgb.r(), color.rgb.g(), color.rgb.b()
                tex_path = color.pFileName
                if tex_path and not tex_path == 'no file':
                    MaxwellLog("LOADING: ", tex_path)
                    i = load_image(tex_path.replace("\\","/"), basepath)
                    if i:
                        textures[tex_path] = i
                        #bpy.data.images.append(i)
                        #MaxwellLog(r,g,b)
        bmat.diffuse_color = (r, g, b)
        if len(textures) > 0:
            MaxwellLog(textures)
            bmat.use_nodes = True
            n = bmat.node_tree.nodes.new('TEX_IMAGE')
            n.image = textures[tex_path]
            bmat.node_tree.links.new(n.outputs['Color'], bmat.node_tree.nodes['Diffuse BSDF'].inputs['Color'] )
        materials[mat.getName()] = bmat
        mat = mat_it.next()
    return materials

def write_instances(context, mxs_scene, ob_dict, materials):
    t1 = time.time()
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
                    MaxwellLog( mat.getName(), " ", ob.material_slots[0].name)
                    ob.material_slots[0].link = 'OBJECT'
                    ob.material_slots[0].material = materials[mat.getName()]
            ob.matrix_basis = CbasePivot2Matrix(base,pivot)
            bpy.context.scene.objects.link(ob)
            instance_count += 1
        obj = it.next()
    t2 = time.time()
    MaxwellLog('imported %d instance in %.4f sec' % (instance_count, (t2 - t1)))

def write_objects(context, mxs_scene, materials):
    t1 = time.time()
    it = CmaxwellObjectIterator()
    obj = it.first(mxs_scene)
    ob_dict = {}
    while obj.isNull() == False:
        if obj.isMesh() == 1:
            name, ob = write_mesh(context,obj,materials)
            ob_dict[name] = ob
        obj = it.next()
    t2 = time.time()
    MaxwellLog('imported %d objects in %.4f sec' % (len(ob_dict), (t2 - t1)))
    return ob_dict

def load(operator, context, filepath):
    '''load a maxwell file'''

    MaxwellLog('importing mxs %r' % filepath)
    basepath, mxs_filename = os.path.split(filepath)

    time_main = time.time()
    mxs_scene = Cmaxwell(mwcallback)

    ok = mxs_scene.readMXS(filepath)
    if ok == 0:
        MaxwellLog('Error reading input file: %s' % (filepath))
        MaxwellLog(mxs_scene.getLastErrorString())

    time_new = time.time()
    MaxwellLog('Done parsing mxs %r in %.4f sec.' % (filepath, (time_new - time_main)))

    for cam_name in mxs_scene.getCameraNames():
      write_camera(context, mxs_scene.getCamera(cam_name))
    context.scene.camera = bpy.data.objects[mxs_scene.getActiveCamera().getName()]

    # READ MATERIALS
    materials = write_materials(context, mxs_scene, basepath)

    ob_dict = write_objects(context, mxs_scene, materials)

    write_instances(context, mxs_scene, ob_dict, materials)


    MaxwellLog(mxs_scene.getSceneInfo()," Triangle groups: ",mxs_scene.getTriangleGroupsCount())

    t2 = time.time()
    MaxwellLog('finished importing: %r in %.4f sec.' %
            (filepath, (t2 - time_main)))
    return {'FINISHED'}

