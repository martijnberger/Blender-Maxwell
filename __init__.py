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


bl_info = {
    "name": "NextLimit Maxwell importer/exporter",
    "author": "Martijn Berger",
    "version": (0, 0, 4, 'dev'),
    "blender": (2, 6, 5),
    "description": "Render scenes with Maxwell render and import/export MXS",
    "warning": "Very early preview",
    "wiki_url": "https://github.com/martijnberger/Blender-Maxwell",
    "tracker_url": "",
    "category": "Render",
    "location": "Info Header > Engine dropdown menu"}

import bpy
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty

if 'core' in locals():
    import imp
    imp.reload(core)
else:
    import bpy

    from extensions_framework import Addon
    MaxwellRenderAddon = Addon(bl_info)
    register, unregister = MaxwellRenderAddon.init_functions()


    # Importing the core package causes extensions_framework managed
    # RNA class registration via @MaxwellRenderAddon.addon_register_class
    from . import core


@MaxwellRenderAddon.addon_register_class
class ExampleAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    camera_far_plane = IntProperty(
            name="Default Camera Distance",
            default=1250,
            )
    draw_bounds = IntProperty(
            name="Draw object as bounds when over",
            default=5000,
            )


    def draw(self, context):
        layout = self.layout
        layout.label(text="MXS import options:")
        layout.prop(self, "camera_far_plane")







