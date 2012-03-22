import sys
import os
import time
import bpy
import mathutils

from bpy_extras.io_utils import unpack_list, unpack_face_list
from bpy_extras.image_utils import load_image

#import pymaxwell
from .pymaxwell import *
#from . import pymaxwell

def load(operator, context, filepath):

    print('\nimporting mxs %r' % filepath)

    time_main = time.time()
    
    mxs_scene = Cmaxwell(mwcallback)
    
    ok = mxs_scene.readMXS(filepath)
    if ok == 0:
        print('\nError reading input file: %s' % (filepath))
        print(mxs_scene.getLastErrorString())
   
    time_new = time.time()
    print('\nDone parsing mxs %r in %.4f sec.' % (filepath, (time_new - time_main)))

    it = CmaxwellObjectIterator()
    obj = it.first(mxs_scene)
    print(type(obj))
    n = 1
    imp=False
    while obj.isNull() == False:
        if(obj.isMesh() == 1):
            if(obj.getNumTriangles() > 0):
                #print("Mesh", obj.getName())
                (base,pivot) = obj.getBaseAndPivot()
                triangles = obj.getNumTriangles()
                vertices = obj.getNumVertexes()
                normals = obj.getNumNormals()
                positions = obj.getNumPositionsPerVertex()
                verts = []
                faces = []
                i = 0
                num = triangles
                my_max = 0
                while i < num:
                    triangle = obj.getTriangle(i)
                    (v1,v2,v3,n1,n2,n3) = triangle
                    my_max = max(my_max,v1,v2,v3)
                    faces.append((v1,v2,v3,v1))
                    i = i + 1
                print("Triangles: ", triangles , "\tVertices:", my_max ,"\tNormals:", normals, "\tPositions:", positions)
                i = 0
                while i <= my_max:
                    vert = obj.getVertex(i,0)
                    verts.append((vert.x(),vert.z(),vert.y()))
                    i = i + 1
                #verts=[(-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, 1.0 ,-1.0), \
                #       (-1.0, 1.0,-1.0), (0.0, 0.0, 1.0)]
                        
                       # Define the faces by index numbers. Each faces is defined by 4 consecutive integers.
                       # For triangles you need to repeat the first vertex also in the fourth position.
                #faces=[ (2,1,0,3), (0,1,4,0), (1,2,4,1), (2,3,4,2), (3,0,4,3)]
                me = bpy.data.meshes.new('Mesh')
                me.from_pydata(verts,[],faces)   # edges or faces should be [], or you ask for problems
                me.update(calc_edges=True)    # Update mesh with new data
                ob = bpy.data.objects.new(str(n), me)
                ob.location = (0.0, 0.0, 0.0)
                ob.show_name = True
                ob.scale = [pivot.xAxis.x(), pivot.zAxis.z(), pivot.yAxis.y()]
                ob.location = [ base.origin.x(), base.origin.z(), base.origin.y()]
                #ob.matrix_world = [pivot.xAxis.x(), pivot.xAxis.z(), pivot.xAxis.y(), 0.0, 
                #                    pivot.zAxis.x(), pivot.zAxis.z(), pivot.zAxis.y(), 0.0,
                #                    pivot.yAxis.x(), pivot.yAxis.z(), pivot.yAxis.y(), 0.0,
                #                    base.origin.x(), base.origin.z(), base.origin.y(), 1.0]

                bpy.context.scene.objects.link(ob)
                
                me.update(calc_edges=True)
                print(base, pivot)
                n = n + 1
                imp=True

        obj = it.next()
        #if imp:
        #    break

    time_new = time.time()
    print('finished importing: %r in %.4f sec.' % (filepath, (time_new - time_main)))
    return {'FINISHED'}



