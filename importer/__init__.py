import bpy
import os
import time
import math

from mathutils import Matrix, Vector
from bpy_extras.io_utils import unpack_list, unpack_face_list
from bpy_extras.image_utils import load_image
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from collections import OrderedDict
from .. import MaxwellRenderAddon

from ..pymaxwell import *
from ..outputs import MaxwellLog

pi = math.pi

def CbasePivot2Matrix(b,p):
    '''Calculate a transformation matrix based on a MXS base and pivot
       FIXME this breaks if pivot.origin != 0 '''
    m = Cbase2Matrix3(b) * Cbase2Matrix3(p)
    x = m[0]
    y = m[1]
    z = m[2]
    return Matrix([(x.x,      z.x,      y.x,      b.origin.x()),
                   (-1 * x.z, -1 * z.z, -1 * y.z, -1 * b.origin.z()),
                   (x.y,      z.y,      y.y,       b.origin.y()),
                   (0.0,        0.0,        0.0,        1.0)])

def Cbase2Matrix4(b):
    x = b.xAxis
    z = b.zAxis
    y = b.yAxis
    return Matrix([(x.x(),      x.y(),      x.z(),      b.origin.x()),
                   (y.x(),      y.y(),      y.z(),       b.origin.y()),
                   (z.x(),      z.y(),      z.z(),       b.origin.z()),
                   (0.0,        0.0,        0.0,        1.0)])

def Cbase2Matrix3(b):
    x = b.xAxis
    z = b.zAxis
    y = b.yAxis
    return Matrix([(x.x(),      x.y(),      x.z()),
                   (y.x(),      y.y(),      y.z()),
                   (z.x(),      z.y(),      z.z())])

def Cvector2Vector(v):
    return Vector((v.x(), -1.0 * v.z(), v.y()))

@MaxwellRenderAddon.addon_register_class
class ImportMXS(bpy.types.Operator, ImportHelper):
    '''load a NextLimit Maxwell MXS file'''
    bl_idname = "import_scene.mxs"
    bl_label = "Import MXS"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".mxs"

    filter_glob = StringProperty(
        default="*.mxs",
        options={'HIDDEN'},
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "split_mode",
            ))
        return SceneImporter().set_filename(keywords['filepath']).load(context)

    def draw(self, context):
        layout = self.layout

menu_func = lambda self, context: self.layout.operator(ImportMXS.bl_idname, text="Import Maxwell Scene(.mxs)")
bpy.types.INFO_MT_file_import.append(menu_func)



class SceneImporter():
    def __init__(self):
        self.filepath = '/tmp/untitled.mxs'

    def set_filename(self, filename):
        self.filepath = filename
        self.basepath, self.mxs_filename = os.path.split(self.filepath)
        return self # allow chaining


    def write_camera(self, camera):
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
      cam.shift_x = shift_x / 200.0
      cam.shift_y = shift_y / -200.0
      # Cycles
      cam.cycles.aperture_fstop = fStop
      # Luxrender
      #cam.luxrender_camera.fstop = fStop
      cam.name = camera.getName()


    def write_mesh(self, obj):
      materials = self.materials
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

        inv_matrix = ob.matrix_basis.inverted()
        bpy.context.scene.objects.link(ob)
        bpy.context.scene.objects.active = ob
        ob.select = True
        bpy.ops.object.transform_apply(rotation=True,scale=True)
        ob.select = False
        me.update(calc_edges=True)
        return (name, (ob, inv_matrix))
      else:
          MaxwellLog('NOT DONE:', obj.getName(), ' NULL: ', obj.isNull(), '  ', obj.getNumVertexes(), '  ', obj.getNumTriangles())
      return (False, False)



    def write_materials(self):
        self.materials = {}
        mat_it = CmaxwellMaterialIterator()
        mat = mat_it.first(self.mxs_scene)
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
                        i = load_image(tex_path.replace("\\","/"), self.basepath)
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
                #bmat.node_tree.links.new(n.outputs['Color'], bmat.node_tree.nodes['Diffuse BSDF'].inputs['Color'] )
            self.materials[mat.getName()] = bmat
            mat = mat_it.next()

    def write_instances(self):
        instances = {}
        t1 = time.time()
        it = CmaxwellObjectIterator()
        obj = it.first(self.mxs_scene)
        instance_count = 0
        while obj.isNull() == False:
            if(obj.isInstance() == 1):
                (base, pivot) = obj.getBaseAndPivot()
                instance_count += 1
                o = obj.getInstanced()
                parent_name = o.getName()
                mat = obj.getMaterial()
                if mat.isNull() == False:
                    mat = mat.getName()
                else:
                    mat = 'None'
                matrix = CbasePivot2Matrix(base,pivot)
                key = (parent_name, mat)
                if key in instances:
                    instances[key].append(matrix)
                else:
                    instances[key] = [matrix]
            obj = it.next()
        MaxwellLog("instances {}, object,color instanced {}".format(instance_count,len(instances)))

        imported_count = 0
        for k, v in instances.items():
            parent_name, mat = k
            max_instances = 200
            if len(v) < max_instances:
                for w in v:
                    ob, inv_matrix = self.ob_dict[parent_name]
                    ob = ob.copy()
                    ls = (w.to_3x3() * inv_matrix.to_3x3() ).to_4x4()
                    ls.col[3] = w.col[3]
                    ob.matrix_basis = ls
                    if len(ob.data.vertices) > 5000:
                        ob.draw_type = 'BOUNDS'
                    if not mat == 'None':
                        ob.material_slots[0].link = 'OBJECT'
                        ob.material_slots[0].material = self.materials[mat]
                    bpy.context.scene.objects.link(ob)
                    imported_count += 1
            else:
                MaxwellLog("{} has more then {} instances skipping: {}".format(parent_name, max_instances,len(v)))
                locations = {}
                for m in v:
                    l = (m.col[3][0], m.col[3][1], m.col[3][2])
                    key = (m[0][0], m[0][1], m[0][2], m[1][0], m[1][1], m[1][2], m[2][0], m[2][1], m[2][2])
                    if key in locations:
                        t = locations[key][1]
                        locations[key][0].append((l[0] - t[0],l[1] - t[1],l[2] - t[2] ))
                    else:
                        locations[key] = ([(0,0,0)], l)



                for trans, ver in locations.items():
                    verts, t = ver
                    MaxwellLog("{} {}: {} locations".format(k[0], trans, len(verts)))
                    dme = bpy.data.meshes.new(k[0])
                    dme.vertices.add(len(verts))
                    dme.vertices.foreach_set("co", unpack_list(verts))
                    dme.update(calc_edges=True)    # Update mesh with new data
                    dme.validate()
                    dob = bpy.data.objects.new("DUPLI" + k[0], dme)
                    dob.dupli_type = 'VERTS'
                    dmatrix = Matrix.Identity(4)
                    dmatrix.col[3] = t[0], t[1], t[2], 1
                    dob.matrix_basis = dmatrix

                    w = Matrix([(trans[0], trans[1], trans[2]), (trans[3], trans[4], trans[5]), (trans[6], trans[7], trans[8])])
                    ob, inv_matrix = self.ob_dict[parent_name]
                    ob = ob.copy()
                    ls = (w * inv_matrix.to_3x3() ).to_4x4()
                    ls.col[3] = verts[0][0],verts[0][1],verts[0][2],1
                    ob.matrix_basis = ls
                    if len(ob.data.vertices) > 5000:
                        ob.draw_type = 'BOUNDS'
                    if not mat == 'None':
                        ob.material_slots[0].link = 'OBJECT'
                        ob.material_slots[0].material = self.materials[mat]

                    ob.parent=dob
                    bpy.context.scene.objects.link(dob)
                    bpy.context.scene.objects.link(ob)


        t2 = time.time()
        MaxwellLog('imported %d of of %d instance in %.4f sec' % (imported_count,instance_count, (t2 - t1)))
        return


    def write_objects(self):
        t1 = time.time()
        it = CmaxwellObjectIterator()
        obj = it.first(self.mxs_scene)
        self.ob_dict = {}
        while obj.isNull() == False:
            if obj.isMesh() == 1:
                name, ob = self.write_mesh(obj)
                self.ob_dict[name] = ob
            obj = it.next()
        t2 = time.time()
        MaxwellLog('imported %d objects in %.4f sec' % (len(self.ob_dict), (t2 - t1)))


    def load(self, context):
        '''load a maxwell file'''
        self.context = context

        MaxwellLog('importing mxs %r' % self.filepath)

        time_main = time.time()
        mxs_scene = Cmaxwell(mwcallback)

        ok = mxs_scene.readMXS(self.filepath)
        if ok == 0:
            MaxwellLog('Error reading input file: %s' % (self.filepath))
            MaxwellLog(mxs_scene.getLastErrorString())
        self.mxs_scene = mxs_scene

        time_new = time.time()
        MaxwellLog('Done parsing mxs %r in %.4f sec.' % (self.filepath, (time_new - time_main)))

        for cam_name in mxs_scene.getCameraNames():
          self.write_camera(mxs_scene.getCamera(cam_name))
        context.scene.camera = bpy.data.objects[mxs_scene.getActiveCamera().getName()]

        # READ MATERIALS
        self.write_materials()

        self.write_objects()

        self.write_instances()


        MaxwellLog(mxs_scene.getSceneInfo()," Triangle groups: ",mxs_scene.getTriangleGroupsCount())

        t2 = time.time()
        MaxwellLog('finished importing: %r in %.4f sec.' %
                (self.filepath, (t2 - time_main)))
        self.mxs_scene.freeScene()
        return {'FINISHED'}

