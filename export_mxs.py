import sys
import os
import time
import bpy
import mathutils
import math

from mathutils import Matrix
from bpy_extras.io_utils import unpack_list, unpack_face_list
from bpy_extras.image_utils import load_image

from .pymaxwell import *

def save(operator, context, filepath=""):

    
    print('\nexporting mxs %r' % filepath)

    time_main = time.time()
    mxs_scene = Cmaxwell(mwcallback)
    mxs_scene.setPluginID("Blender Maxwell")
    mxs_scene.setInputDataType('YZXRH')

    camera = context.scene.camera
    res = export_camera(camera,mxs_scene, round(context.scene.render.resolution_x * (context.scene.render.resolution_percentage / 100)),
                                          round(context.scene.render.resolution_y * (context.scene.render.resolution_percentage / 100)) )
    res.setActive()

    for o in context.scene.objects:
        if(o.type == 'MESH'):
            me = o.to_mesh(context.scene, True, 'RENDER')
            export_mesh(o, me, mxs_scene)

    print(mxs_scene.getSceneInfo())

    ok = mxs_scene.writeMXS(filepath)

    if ok == 0:
        print("Error saving ")

    mxs_scene.freeScene()
    time_new = time.time() 
    print('finished exporting: %r in %.4f sec.' %
            (filepath, (time_new - time_main)))
    return {'FINISHED'}

# export the given Blender camera into the maxwell scene
def export_camera(camera, mxs_scene, res_x, res_y):
    matrix = camera.matrix_world.copy()
    pos = matrix.col[3]
    direct = matrix.col[2]
    up = pos + matrix.col[1]
    
    sensor_width = 0.0350
    sensor_height = 0.0350 * (res_y / res_x)
    #               addCamera( name, nSteps, shutter, filmWidth, filmHeight, iso, 
    #                          diaphragmType,  angle, nBlades, fps, 
    #                           xRes, yRes, pixelAspect, proyectionType = 0 )   
    res = mxs_scene.addCamera( camera.name, 1, 500, sensor_width, sensor_height, 100  
                             , "Circular" , 60 ,8 , 24 
                             , res_x, res_y , 1  , 0 )

    if res == 0:
        print("Adding camera failed")
    mxs_camera = res
    
    #figure out position, rot and look-at
    position = Cvector()
    position.assign(pos[0],pos[2],pos[1])
    up_vec = Cvector()
    up_vec.assign(up[0],up[2],up[1])
    tar_vec = Cvector()
    tar_vec.assign(direct[0],direct[2],direct[1])
    #set the values as step 0 for now TODO: add motion blur support
    focal_length = camera.data.lens / 1000
    mxs_camera.setStep(0,position,tar_vec,up_vec,focal_length,5.6,0)
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
        normal = Cvector()
        # XXX check why we are getting NaN's
        normal.assign(vertex.normal[0] if not math.isnan(vertex.normal[0]) else 0 ,
                      vertex.normal[1] if not math.isnan(vertex.normal[1]) else 0,
                      vertex.normal[2] if not math.isnan(vertex.normal[2]) else 0)
        verts[i] = position
        normals[i] = normal

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

    #construct base and pivot we need to account for transformations
    #setBaseAndPivot(Cbase base, Cbase pivot, float substepTime = 0.0 )
    m = mesh.matrix_world
    base_o = Cvector(m[0][3],m[1][3],m[2][3])
    base_x = Cvector(m[0][0],m[1][0],m[2][0])
    base_y = Cvector(m[0][1],m[1][1],m[2][1])
    base_z = Cvector(m[0][2],m[1][2],m[2][2])
    base = Cbase(base_o,base_x,base_y,base_z)

    pivot_o = Cvector(0,0,0)
    pivot_x = Cvector(1,0,0)
    pivot_y = Cvector(0,1,0) 
    pivot_z = Cvector(0,0,1)
    pivot = Cbase(pivot_o,pivot_x,pivot_y,pivot_z)
    mxs_object.setBaseAndPivot(base,pivot)


      
