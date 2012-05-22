bl_info = {
    "name": "NextLimit Maxwell format",
    "author": "Martijn Berger",
    "version": (0, 0, 1, 'dev'),
    "blender": (2, 6, 2),
    "description": "Render scenes with Maxwell render and import/export MXS",
    "warning": "Very early preview",
    "wiki_url": "http://www.nextlimit.com",
    "tracker_url": "",
    "category": "Render",
    "location": "Render > Engine > Maxwell"}

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

from extensions_framework import Addon
from imp import reload # this can go once its stable

MaxwellAddon = Addon(bl_info)

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
        from . import export_mxs
        reload(export_mxs)
        keywords = self.as_keywords(ignore=("axis_forward",
                                "axis_up",
                                "global_scale",
                                "check_existing",
                                "filter_glob",
                                ))

        return export_mxs.save(self, context, **keywords)

    def draw(self, context):
        layout = self.layout

        
def menu_func_import(self, context):
    self.layout.operator(ImportMXS.bl_idname, text="Maxwell (.mxs)")


def menu_func_export(self, context):
    self.layout.operator(ExportMXS.bl_idname, text="Maxwell (.mxs)")
    

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)



def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
