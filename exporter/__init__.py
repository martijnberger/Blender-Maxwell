import time
import math
import mathutils
from mathutils import Matrix, Vector

from ..outputs import MaxwellLog

from ..pymaxwell import *


pi = math.pi
TRANSFORM_MATRIX = mathutils.Matrix().Rotation( -pi /2 , 4, 'X')  # rotate -90 degree around the x axis

def Matrix2CbaseNPivot(m):
    m = TRANSFORM_MATRIX * m
    base = Cbase()
    base.origin = toCvector(m.col[3])
    base.xAxis = toCvector([1,0,0])
    base.yAxis = toCvector([0,1,0])
    base.zAxis = toCvector([0,0,1])

    pivot = Matrix2Cbase(m)

    return base, pivot

def Matrix2Cbase(m):
    return Cbase(Cvector(0,0,0), toCvector(m.col[0]), toCvector(m.col[1]),toCvector(m.col[2]))

def toCvector(vec):
    '''create a Cvector type from a blender mathutils.Vector'''
    return Cvector(vec[0],vec[1],vec[2])

def save(operator, context, filepath=""):
    '''main scene exporter logic '''
    MaxwellLog('exporting mxs %r' % filepath)

    time_main = time.time()
    mxs_scene = Cmaxwell(mwcallback)
    mxs_scene.setPluginID("Blender Maxwell")
    mxs_scene.setInputDataType('YZXRH')

    for o in context.scene.objects:
        if(o.type == 'MESH' and o.is_visible(context.scene)):
            me = o.to_mesh(context.scene, True, 'RENDER')
            export_mesh(o, me, mxs_scene)
        elif(o.type == 'CAMERA' and o.is_visible(context.scene)):
            res = export_camera(o,mxs_scene, round(context.scene.render.resolution_x * (context.scene.render.resolution_percentage / 100)),
                                                  round(context.scene.render.resolution_y * (context.scene.render.resolution_percentage / 100)) )
            if(context.scene.camera.name == o.name):
                res.setActive()
        elif(o.type == 'EMPTY'):
            MaxwellLog('ignore: EMPTY')
        else:
            MaxwellLog('ignoring object', o.type)
 

    print(mxs_scene.getSceneInfo())

    try:
        ok = mxs_scene.writeMXS(filepath)
    except Exception as e:
        MaxwellLog(e)
        MaxwellLog("Error saving ")
        mxs_scene.freeScene()
        return {'FINISHED'}



    if ok == 0:
        MaxwellLog("Error saving ")

    mxs_scene.freeScene()
    time_new = time.time()
    MaxwellLog('finished exporting: %r in %.4f sec.' %
            (filepath, (time_new - time_main)))
    return {'FINISHED'}

# export the given Blender camera into the maxwell scene
def export_camera(camera, mxs_scene, res_x, res_y):
    #figure out position, rot and look-at
    matrix = TRANSFORM_MATRIX * camera.matrix_world.copy()
    pos = (matrix.col[3])
    direct = ((matrix.col[3] - matrix.col[2]))
    up = matrix.col[1].to_3d().normalized()
   
    sensor_width = camera.data.sensor_width / 1000.0
    sensor_height = camera.data.sensor_height / 1000.0
    res = mxs_scene.addCamera( camera.name, 1, 1/100, sensor_width, sensor_height, 100  
                             , "Circular" , (camera.data.angle / math.pi) * 180, 8, 24 
                             , res_x, res_y , 1  , 0 )
    if res == 0:
        MaxwellLog("Adding camera failed")
        return
    mxs_camera = res
    
    position = toCvector(pos)
    up_vec = toCvector(up)
    tar_vec = toCvector(direct)
    #set the values as step 0 for now TODO: add motion blur support
    focal_length = camera.data.lens / 1000
    fStop = camera.data.cycles.aperture_fstop if camera.data.cycles else 5.6
    mxs_camera.setStep(0, position, tar_vec, up_vec, focal_length, fStop , 0)
    return mxs_camera

def export_mesh(mesh, me, mxs_scene):
    # some structures to keep stuff while we figure out how much it is
    verts = {}
    normals = {}
    faces = []
    for i, vertex in enumerate(me.vertices):
        #print(i,": ", vertex.co)
        position = Cvector()
        position.assign(vertex.co[0],vertex.co[1],vertex.co[2])
        verts[i] = position
        normals[i] = toCvector(Vector((vertex.normal[0],vertex.normal[1],vertex.normal[2])).normalized())

    for i, face in enumerate(me.tessfaces):
        faces.append((face.vertices[0],face.vertices[1],face.vertices[2]))
        if(len(face.vertices) == 4):
            faces.append((face.vertices[2],face.vertices[3],face.vertices[0]))

    #create actual maxwell object
    mxs_object = mxs_scene.createMesh(mesh.name, len(verts), len(normals),len(faces),1) 

    #dump in stuff into the object
    for i, v in verts.items():
        mxs_object.setVertex(i, 0, v)

    for i, n in normals.items():
        mxs_object.setNormal(i, 0, n)

    for i, f in enumerate(faces):
        mxs_object.setTriangle(i, f[0], f[1], f[2], f[0], f[1], f[2])

    base, pivot = Matrix2CbaseNPivot(mesh.matrix_world)
    mxs_object.setBaseAndPivot(base,pivot)


      
