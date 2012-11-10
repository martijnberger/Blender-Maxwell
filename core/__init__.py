import bpy
import threading

__author__ = 'mberger'

from .. import MaxwellRenderAddon



@MaxwellRenderAddon.addon_register_class
class RENDERENGINE_maxwell(bpy.types.RenderEngine):
    '''
    Maxwell Engine
    '''
    bl_idname     = 'MAXWELL_RENDER'
    bl_label      = 'Maxwell'
    bl_use_preview    = True

    render_lock = threading.Lock()

    def update(self, data, scene):
        pass
    def render(self, scene):
        pass

    def preview_update(self, context, id):
        pass
    def preview_render(self):
        pass

    def view_update(self, context):
        pass
    def view_draw(self, context):
        pass