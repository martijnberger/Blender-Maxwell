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

import bpy, bl_ui
import threading

__author__ = 'mberger'

from .. import MaxwellRenderAddon

from ..outputs import MaxwellLog

from ..properties import render
from ..importer import ImportMXS
from ..exporter import ExportMXS
from ..ui import render_panel

def _register_elm(elm, required=False):
    try:
        elm.COMPAT_ENGINES.add('MAXWELL_RENDER')
    except:
        if required:
            MaxwellLog('Failed to add Maxwell to ' + elm.__name__)


_register_elm(bl_ui.properties_render.RENDER_PT_render, required=True)
_register_elm(bl_ui.properties_render.RENDER_PT_dimensions, required=True)
_register_elm(bl_ui.properties_render.RENDER_PT_output, required=True)
_register_elm(bl_ui.properties_render.RENDER_PT_stamp)



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
        print("RENDER")
        pass

    def preview_update(self, context, id):
        pass
    def preview_render(self):
        pass

    def view_update(self, context):
        pass
    def view_draw(self, context):
        pass