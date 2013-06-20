import bpy
from bpy_extras.io_utils import ImportHelper, axis_conversion
from bpy.props import StringProperty, BoolProperty
from .. import MaxwellRenderAddon
from ..maxwell import maxwell

from .SceneImporter import SceneImporter

@MaxwellRenderAddon.addon_register_class
class ImportMXS(bpy.types.Operator, ImportHelper):
    """load a NextLimit Maxwell MXS file"""
    bl_idname = "import_scene.mxs"
    bl_label = "Import MXS"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".mxs"

    filter_glob = StringProperty(
        default="*.mxs",
        options={'HIDDEN'},
    )

    import_camera = BoolProperty(
        name="Cameras",
        description="Import camera's",
        default=True,
    )

    import_material = BoolProperty(
        name="Materials",
        description="Import materials's",
        default=True,
    )

    import_meshes = BoolProperty(
        name="Meshes",
        description="Import meshes's",
        default=True,
    )

    import_instances = BoolProperty(
        name="Instances",
        description="Import instances's",
        default=True,
    )

    apply_scale = BoolProperty(
        name="Apply Scale",
        description="Apply scale to imported objects",
        default=True,
    )

    handle_proxy_group = BoolProperty(
        name="Proxy",
        description="Attempt to find groups for meshes names *_proxy*",
        default=True,
    )

    def execute(self, context):
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "split_mode",
            ))
        return SceneImporter().set_filename(keywords['filepath']).load(context, **keywords)

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.prop(self, "import_camera")
        row.prop(self, "import_material")
        row = layout.row(align=True)
        row.prop(self, "import_meshes")
        row.prop(self, "import_instances")
        row = layout.row(align=True)
        row.prop(self, "handle_proxy_group")
        row.prop(self, "apply_scale")

menu_func = lambda self, context: self.layout.operator(ImportMXS.bl_idname, text="Import Maxwell Scene(.mxs)")
bpy.types.INFO_MT_file_import.append(menu_func)





