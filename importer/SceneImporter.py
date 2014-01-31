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

import bpy
import os
import re
import time

from collections import OrderedDict
from mathutils import Matrix, Vector
from bpy_extras.io_utils import unpack_list, unpack_face_list
from ..maxwell import maxwell

from .util import *
from ..outputs import MaxwellLog


def translate_material(mat, basepath):
    """
        mat -> refrence to the maxwell material
        basepath -> string that references filepath where we look for referenced texture files
    """
    bmat = bpy.data.materials.new(mat.name)
    r, g, b = 0.7, 0.7, 0.7
    textures = {}
    #MaxwellLog("Laoding Material: {}".format(mat_name))
    if mat.getNumLayers() > 0:
        layer = mat.getLayer(0)
        if layer.getNumBSDFs() > 0:
            bsdf = layer.getBSDF(0)
            refl = bsdf.getReflectance()
            color = refl.getColor('color')
            r, g, b = color.rgb.r, color.rgb.g, color.rgb.b
            tex_path = color.pFileName
            if tex_path:
                tex = str(tex_path,'UTF-8').replace("\\","/")
                MaxwellLog("LOADING: {}".format(tex))
                tp = basepath + "/" + tex
                try:
                    i = bpy.data.images.load(tp)
                except RuntimeError:
                    i = None
                if i:
                    textures[tex] = i
    bmat.diffuse_color = (r, g, b)
    if len(textures) > 0:
        MaxwellLog(textures)
        bmat.use_nodes = True
        if bpy.app.version > (2,66,2): #pynodes merge ?
            n = bmat.node_tree.nodes.new('ShaderNodeTexImage')
        else:
            n = bmat.node_tree.nodes.new('TEX_IMAGE')
        n.image = textures[tex]
        try:
            bmat.node_tree.links.new(n.outputs['Color'], bmat.node_tree.nodes['Diffuse BSDF'].inputs['Color'] )
        except KeyError as e:
            print(e)
            pass
    return bmat

class SceneImporter():
    def __init__(self):
        self.filepath = '/tmp/untitled.mxs'
        self.name_mapping = {}

    def set_filename(self, filename):
        self.filepath = filename
        self.basepath, self.mxs_filename = os.path.split(self.filepath)
        return self # allow chaining


    def write_camera(self, camera):
      #MaxwellLog("Camera: {}".format(camera.getName()))
      origin, focalPoint, up, focalLength, fStop, stepTime = camera.getStep(0)
      camValues = camera.getValues()
      bpy.ops.object.add(type='CAMERA', location=AxisMatrix3 * Cvector2Vector(origin))
      ob = self.context.object

      z = AxisMatrix3 * Cvector2Vector(origin) - AxisMatrix3 *Cvector2Vector(focalPoint)
      z = z.normalized()
      y = (AxisMatrix3 *Cvector2Vector(up)).normalized()
      x = y.cross(z)

      ob.matrix_world.col[0] = x.resized(4)
      ob.matrix_world.col[1] = y.resized(4)
      ob.matrix_world.col[2] = z.resized(4)

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
      cam.clip_end = self.prefs.camera_far_plane
      cam.name = camera.getName()


    def write_mesh_data(self, obj, name):
        '''
            Convert maxwell object into blender mesh datablock
            precond: check that obj != null and that it is actually a mesh
        '''
        uv_layer_count = obj.getNumChannelsUVW()
        verts = []
        faces = []
        normals = []
        vert_norm = {}
        mats = {}
        mat_index = []
        uvs = []
        max_vertex = 0
        max_normal = 0
        for i in range(obj.getNumTriangles()):
            triangle = obj.getTriangle(i)
            (v1, v2, v3, n1, n2, n3) = triangle
            max_vertex = max(max_vertex, v1, v2, v3)
            max_normal = max(max_normal, n1, n2, n3)
            mat = obj.getTriangleMaterial(i)
            if not mat.isNull():
              mat_name = mat.name
              if not mat_name in mats:
                mats[mat_name] = len(mats)
              mat_index.append(mats[mat_name])
            else:
              mat_index.append(0)
            if v3 == 0: # eeekadoodle dance
                faces.append((v2, v3, v1))
                zero_face_start = True
            else:
                faces.append((v1, v2, v3))
                zero_face_start = False
            vert_norm[v1] = n1
            vert_norm[v2] = n2
            vert_norm[v3] = n3
            if uv_layer_count > 0:
              u1, v1, w1, u2, v2, w2, u3, v3, w3 = obj.getTriangleUVW(i, 0)
              if not zero_face_start:
                  uvs.append(( u1, -1.0 * v1,
                               u2, -1.0 * v2,
                               u3, -1.0 * v3, 0.0, 0.0 ))
              else:
                  uvs.append((
                               u2, -1.0 * v2,
                               u3, -1.0 * v3, u1, -1.0 * v1, 0.0, 0.0 ))

            else:
                uvs.append((0.0, 0.0, 0.0, 0.0, 0.0 ,0.0 ,0.0, 0.0))

        for i in range(max_vertex + 1):
            vert = obj.getVertex(i, 0)
            verts.append((vert.x, vert.y, vert.z))
        for i in range(max_vertex + 1):
            n = obj.getNormal(vert_norm[i],0)
            normals.append((n.x, n.y, n.z))

        me = bpy.data.meshes.new(name)
        me.vertices.add(len(verts))
        me.tessfaces.add(len(faces))
        if len(mats) >= 1:
            mats_sorted = OrderedDict(sorted(mats.items(), key=lambda x: x[1]))
            for k in mats_sorted.keys():
                me.materials.append(self.materials[k])
        else:
            MaxwellLog("WARNING OBJECT {} HAS NO MATERIAL".format(obj.getName()))

        me.vertices.foreach_set("co", unpack_list(verts))
        me.vertices.foreach_set("normal",  unpack_list(normals))
        me.tessfaces.foreach_set("vertices_raw", unpack_face_list(faces))
        me.tessfaces.foreach_set("material_index", mat_index)
        if len(uvs) > 0:
            me.tessface_uv_textures.new()
            for i in range(len(faces)):
                me.tessface_uv_textures[0].data[i].uv_raw = uvs[i]

        me.update(calc_edges=True)    # Update mesh with new data
        me.validate()
        return me, len(verts)


    def cleanup_name(self, name):
        '''
            Create a better name
        '''
        # TODO FIXME should check to see if we insert a double
        if name in self.name_mapping:
            return self.name_mapping[name]
        MaxwellLog('cleaning up {} -> '.format(name, re.match('<(.*)>', name)))
        try: # strip of ' [0.0.0]' and alike
            bettername = re.match('(.*) \[\d{1,3}\.\d{1,3}\.\d{1,3}\]', name).group(1)
        except AttributeError as err:
            bettername = name
        try: # strip of '[0]' and alike
            bettername = re.match('(.*)\[\d{1,3}\]', bettername).group(1)
        except AttributeError as err:
            pass
        while bettername[0] == " ":
            bettername = bettername[1:]
        while name in self.name_mapping:
            name += '_'
        else: # we found a unique name, lets insert it
            self.name_mapping[name] = bettername
            return bettername

    def find_blender_group(self, name):
        if '#' in name:
            name = re.match('(.*)#', name).group(0)
        bettername = name[:-6]
        if bettername in bpy.data.groups.keys():
            #MaxwellLog("FOUND {} GROUP".format(bettername))
            return True, bettername
        else:
            MaxwellLog("COULD NOT FIND GROUP FOR {}".format(bettername))
            return False, name

    def write_mesh_object(self, obj, **options):
        """
            Write a Blender object based on the Maxwell object without any instances.
        """
        n = 1
        if (not obj.isNull()) and obj.isMesh() and (obj.getNumTriangles() > 0 and obj.getNumVertexes() > 0):
            try:
                name = obj.getName()
            except UnicodeDecodeError:
                obj.setName('corrupt' + str(n))
                name = 'corrupt' + str(n)
                n += 1

            name = self.cleanup_name(name)

            if 'proxy' in name:
                proxy_group, name = self.find_blender_group(name)
            else:
                proxy_group = False

            base, pivot = obj.getBaseAndPivot()

            if not proxy_group:
                me, num_verts = self.write_mesh_data(obj, name)
                ob = bpy.data.objects.new(name, me)
                if num_verts > self.prefs.draw_bounds:
                    ob.draw_type = 'BOUNDS'
                me.update(calc_edges=True)
            else:
                ob = bpy.data.objects.new(name, None)
                ob.dupli_type = 'GROUP'
                ob.dupli_group = bpy.data.groups[name]


            if not proxy_group:
                ob.matrix_world = CbasePivot2Matrix(base,pivot)
            else:
                matr = CbasePivot2Matrix(base,pivot)
                matr2 = (axis_conversion(from_forward='Y', from_up='Z', to_forward='-Z', to_up='Y') * Matrix.Scale(1 / 0.0254, 3) * matr.to_3x3()).to_4x4()
                matr2.col[3] = matr.col[3]
                ob.matrix_world = matr2

            self.context.scene.objects.link(ob)
            self.context.scene.objects.active = ob


            if options['apply_scale']:
                try:
                    inv_matrix = ob.matrix_basis
                    inv_matrix = inv_matrix.to_3x3().inverted().to_4x4()
                    #MaxwellLog("INV: {}".format(inv_matrix))
                except ValueError:
                    MaxwellLog("Cannot invert {}".format(ob.matrix_basis))
                    inv_matrix = Matrix.Identity(4)
            else:
                inv_matrix = Matrix.Identity(4)


            if not proxy_group and options['apply_scale']:
                ob.select = True
                bpy.ops.object.transform_apply(rotation=True,scale=True)
                ob.select = False
            else:   # not applying scale so inverted operation is identity matrix
                pass
                #inv_matrix = Matrix.Identity(4)

            return name, (ob, inv_matrix, proxy_group)
        else:
            MaxwellLog('NOT DONE:', obj.getName(), ' NULL: ', obj.isNull(), '  ', obj.getNumVertexes(), '  ', obj.getNumTriangles())
            return None, None


    def write_materials(self):
        '''
            Convert Maxwell material to a blender cycles material
        '''
        self.materials = {}
        MaxwellLog("write_materials : iter")
        for mat in self.mxs_scene.getMaterialsIterator():
            if mat.isNull():
                continue
            mat_name = mat.name
            rmat_name = mat_name.rstrip('1234567890')
            if mat_name in self.context.blend_data.materials:
                self.materials[mat_name] = self.context.blend_data.materials[mat_name]
            elif rmat_name in self.context.blend_data.materials:
                self.materials[mat_name] = self.context.blend_data.materials[rmat_name]
            elif rmat_name.lower() in self.context.blend_data.materials:
                self.materials[mat_name] = self.context.blend_data.materials[rmat_name.lower()]
            else:
                self.materials[mat_name] = translate_material(mat, self.basepath)

    def write_instances(self):
        '''
            Attempt to convert maxwell intances to something like a dupligroup or better.
        '''
        instances = {}
        t1 = time.time()
        instance_count = 0

        for obj in self.mxs_scene.getObjectIterator():
            if obj.isInstance() == 1:
                (base, pivot) = obj.getBaseAndPivot()
                instance_count += 1
                o = obj.getInstanced()
                parent_name = self.cleanup_name(o.getName())
                mat = obj.getMaterial()
                if not mat.isNull():
                    mat = mat.name
                else:
                    mat = 'None'
                matrix = CbasePivot2Matrix(base,pivot)
                key = (parent_name, mat)
                if key in instances:
                    instances[key].append(matrix)
                else:
                    instances[key] = [matrix]
            #obj = it.next()
        MaxwellLog("instances {}, object,color instanced {}".format(instance_count,len(instances)))

        imported_count = 0
        for k, v in instances.items():
            parent_name, mat = k

            max_instances = self.prefs.max_instance
            if not parent_name in self.ob_dict:
                MaxwellLog('Cannot find object to instance: {}'.format(parent_name))
                continue
            if len(v) < max_instances:
                for w in v:
                    try:
                        ob, inv_matrix, proxy_group = self.ob_dict[parent_name]
                        ob = ob.copy()
                        ls = (w.to_3x3() * inv_matrix.to_3x3() ).to_4x4()
                        ls.col[3] = w.col[3]
                        if not proxy_group:
                            ob.matrix_basis = ls
                            if len(ob.data.vertices) > 5000:
                                ob.draw_type = 'BOUNDS'
                            if not mat == 'None':
                                try:
                                    ob.material_slots[0].link = 'OBJECT'
                                    ob.material_slots[0].material = self.materials[mat]
                                except IndexError:
                                    pass
                        else:
                            #ob.matrix_basis = MatrixScale(ls)
                            ob.matrix_basis = ls

                        self.context.scene.objects.link(ob)
                        imported_count += 1
                    except KeyError:
                        pass
            else:
                locations = {}
                for m in v:
                    l = (m.col[3][0], m.col[3][1], m.col[3][2])
                    key = (m[0][0], m[0][1], m[0][2], m[1][0], m[1][1], m[1][2], m[2][0], m[2][1], m[2][2])
                    if key in locations:
                        t = locations[key][1]
                        locations[key][0].append((l[0] - t[0],l[1] - t[1],l[2] - t[2] ))
                    else:
                        locations[key] = ([(0,0,0)], l)
                MaxwellLog("{} has more then {} instances ({}) creating {} duplivert groups".format(parent_name, max_instances,len(v),len(locations)))



                for trans, ver in locations.items():
                    verts, t = ver
                    #MaxwellLog("{} : {} locations".format(k[0], len(verts)))
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

                    w = Matrix([(trans[0], trans[1], trans[2]),
                                (trans[3], trans[4], trans[5]),
                                (trans[6], trans[7], trans[8])])
                    ob, inv_matrix, proxy_group = self.ob_dict[parent_name]
                    ob = ob.copy()
                    ls = (w * inv_matrix.to_3x3() ).to_4x4()
                    ls.col[3] = verts[0][0],verts[0][1],verts[0][2],1
                    if not proxy_group:
                        ob.matrix_basis = ls
                        if len(ob.data.vertices) > 5000:
                            ob.draw_type = 'BOUNDS'
                        if not mat == 'None':
                            try:
                                ob.material_slots[0].link = 'OBJECT'
                                ob.material_slots[0].material = self.materials[mat]
                            except IndexError:
                                pass
                    else:
                        ob.matrix_basis = ls
                        #ob.matrix_basis = MatrixScale(ls)

                    ob.parent=dob
                    self.context.scene.objects.link(dob)
                    self.context.scene.objects.link(ob)


        t2 = time.time()
        MaxwellLog('imported %d of of %d instance in %.4f sec' % (imported_count,instance_count, (t2 - t1)))
        return


    def write_objects(self, **options):
        t1 = time.time()
        self.ob_dict = {}
        for obj in self.mxs_scene.getObjectIterator():
            if (not obj.isNull()) and obj.isMesh():
                name, ob = self.write_mesh_object(obj, **options)
                self.ob_dict[name] = ob
        t2 = time.time()
        MaxwellLog('imported %d objects in %.4f sec' % (len(self.ob_dict), (t2 - t1)))


    def load(self, context, **options):
        """load a maxwell file"""
        self.context = context

        MaxwellLog('importing mxs %r' % self.filepath)

        addon_name = __name__.split('.')[0]
        self.prefs = addon_prefs = context.user_preferences.addons[addon_name].preferences

        time_main = time.time()
        mxs_scene = maxwell.maxwell()

        try:
            mxs_scene.readMXS(self.filepath)
        except Exception as e:
            MaxwellLog('Error reading input file: %s' % self.filepath)
            MaxwellLog(e)
        self.mxs_scene = mxs_scene

        time_new = time.time()
        MaxwellLog('Done parsing mxs %r in %.4f sec.' % (self.filepath, (time_new - time_main)))

        if options['import_camera']:
            for cam in mxs_scene.getCamerasIterator():
                self.write_camera(cam)
            context.scene.camera = bpy.data.objects[mxs_scene.getActiveCamera().getName()]

        if options['import_material']:
            # READ MATERIALS
            self.write_materials()

        if options['import_meshes']:
            self.write_objects(**options)
        if options['import_instances']:
            self.write_instances()


        t2 = time.time()
        MaxwellLog('finished importing: %r in %.4f sec.' %
                (self.filepath, (t2 - time_main)))
        self.mxs_scene.freeScene()
        return {'FINISHED'}
