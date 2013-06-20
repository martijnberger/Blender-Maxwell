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

# contains a lot of code inspired / shamelessly copied from luxblend25

from extensions_framework import log

def MaxwellLog(*args, popup=False):
    '''
    Send string to AF log, marked as belonging to Mitsuba module.
    Accepts variable args
    '''
    if len(args) > 0:
        log(' '.join(['%s'%a for a in args]), module_name='Maxwell', popup=popup)