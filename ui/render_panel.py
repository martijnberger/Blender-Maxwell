__author__ = 'mberger'

from .. import MaxwellRenderAddon

import bpy, bl_ui

from extensions_framework.ui import property_group_renderer

class render_panel(bl_ui.properties_render.RenderButtonsPanel, property_group_renderer):
    '''
    Base class for render engine settings panels
    '''

    COMPAT_ENGINES = 'MAXWELL_RENDER'


@MaxwellRenderAddon.addon_register_class
class networking(render_panel):
    '''
    Networking settings UI Panel
    '''

    bl_label = 'Render Options'
    #bl_options = {'DEFAULT_CLOSED'}

    display_property_groups = [
        ( ('scene',), 'maxwell_engine' )
    ]

    def draw(self, context):
        super().draw(context)
