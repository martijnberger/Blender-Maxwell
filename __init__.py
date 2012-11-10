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
#
# ***** END GPL LICENCE BLOCK *****
#

bl_info = {
    "name": "NextLimit Maxwell importer/exporter",
    "author": "Martijn Berger",
    "version": (0, 0, 2, 'dev'),
    "blender": (2, 6, 4),
    "description": "Render scenes with Maxwell render and import/export MXS",
    "warning": "Very early preview",
    "wiki_url": "http://www.nextlimit.com",
    "tracker_url": "",
    "category": "Render",
    "location": "Info Header > Engine dropdown menu"}


if 'core' in locals():
    import imp
    imp.reload(core)
elif 'importer' in locals():
    import imp
    imp.reload(importer)
elif 'exporter' in locals():
    import imp
    imp.reload(exporter)
else:
    import bpy

    from extensions_framework import Addon
    MaxwellRenderAddon = Addon(bl_info)
    register, unregister = MaxwellRenderAddon.init_functions()

    # Importing the core package causes extensions_framework managed
    # RNA class registration via @MaxwellRenderAddon.addon_register_class
    from . import core

    from . import exporter
    from . import importer





