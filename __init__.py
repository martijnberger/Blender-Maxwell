bl_info = {
    "name": "NextLimit Maxwell format",
    "author": "Martijn Berger",
    "blender": (2, 6, 0),
    "location": "File > Import-Export",
    "description": "Import-Export MXS",
    "warning": "Very early preview",
    "wiki_url": "http://www.nextlimit.com",
    "tracker_url": "",
    "category": "Import-Export"}

if "bpy" in locals():
    import imp
    if "import_mxs" in locals():
        imp.reload(import_mxs)


import bpy
from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       )
from bpy_extras.io_utils import (ExportHelper,
                                 ImportHelper,
                                 path_reference_mode,
                                 axis_conversion,
                                 )


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
        from . import import_mxs
        keywords = self.as_keywords(ignore=("axis_forward",
                                "axis_up",
                                "filter_glob",
                                "split_mode",
                                ))


        return import_mxs.load(self, context, **keywords)

    def draw(self, context):
        layout = self.layout


def menu_func_import(self, context):
    self.layout.operator(ImportMXS.bl_idname, text="Maxwell (.mxs)")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)
