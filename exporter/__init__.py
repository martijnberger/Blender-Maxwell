import time
import math
import bpy
import mathutils
from mathutils import Matrix, Vector
from bpy_extras.io_utils import ExportHelper
from ..outputs import MaxwellLog
from bpy.props import StringProperty

#from ..pymaxwell import *
from .. import MaxwellRenderAddon

@MaxwellRenderAddon.addon_register_class
class ExportMXS(bpy.types.Operator, ExportHelper):
    '''export as NextLimit Maxwell MXS file'''
    bl_idname = "export_scene.mxs"
    bl_label = "Export MXS"
    bl_options = {'PRESET'}

    filename_ext = ".mxs"

    filter_glob = StringProperty(
        default="*.mxs",
        options={'HIDDEN'},
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "global_scale",
                                            "check_existing",
                                            "filter_glob",
            ))

        return save(self, context, **keywords)

    def draw(self, context):
        layout = self.layout


menu_func = lambda self, context: self.layout.operator(ExportMXS.bl_idname, text="Export Maxwell Scene (.mxs)")
bpy.types.INFO_MT_file_export.append(menu_func)


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

object_cache = {}

def save(operator, context, filepath=""):
    '''main scene exporter logic '''
    MaxwellLog('exporting mxs %r' % filepath)

    time_main = time.time()
    mxs_scene = Cmaxwell(mwcallback)
    mxs_scene.setPluginID("Blender Maxwell")
    mxs_scene.setInputDataType('YZXRH')

    for o in context.scene.objects:
        if(o.type == 'MESH' and o.is_visible(context.scene) and not o.is_duplicator):
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
    shift_x,  shift_y =  camera.data.shift_x * 200.0, camera.data.shift_y * -200.0
    mxs_camera.setShiftLens(shift_x,  shift_y)
    return mxs_camera

def export_mesh(object, me, mxs_scene):

    global object_cache
    mesh_cache_key = object.data

    if mesh_cache_key in object_cache:
        MaxwellLog("Instancing {}".format(mesh_cache_key))
        orig_mxs_object, i = object_cache[mesh_cache_key]
        i += 1
        name = object.name + str(i)
        MaxwellLog(i)
        mxs_object = mxs_scene.createInstancement(name,orig_mxs_object)
        object_cache[mesh_cache_key] = (orig_mxs_object, i)
    else:
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

        MaxwellLog(object)
        MaxwellLog(object.name)
        #create actual maxwell object
        mxs_object = mxs_scene.createMesh(object.name, len(verts), len(normals),len(faces),1)

        MaxwellLog(mxs_object)
        if mxs_object != None:
            #dump in stuff into the object
            for i, v in verts.items():
                mxs_object.setVertex(i, 0, v)

            for i, n in normals.items():
                mxs_object.setNormal(i, 0, n)

            for i, f in enumerate(faces):
                mxs_object.setTriangle(i, f[0], f[1], f[2], f[0], f[1], f[2])
        else:
            MaxwellLog('could not create {}'.format(object.name))

    base, pivot = Matrix2CbaseNPivot(object.matrix_world)
    mxs_object.setBaseAndPivot(base,pivot)
    if not mesh_cache_key in object_cache:
        object_cache[mesh_cache_key] = (mxs_object, 0)



      
