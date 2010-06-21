# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Ranger - file browser for the unix terminal"""

import os
import sys
from ranger.ext.openstruct import OpenStruct

__license__ = 'GPL3'
__version__ = '1.1.1'
__credits__ = 'Roman Zimbelmann'
__author__ = 'Roman Zimbelmann'
__maintainer__ = 'Roman Zimbelmann'
__email__ = 'romanz@lavabit.com'

__copyright__ = """
Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
"""

USAGE = '%prog [options] [path/filename]'
DEFAULT_CONFDIR = '~/.ranger'
RANGERDIR = os.path.dirname(__file__)
LOGFILE = '/tmp/errorlog'
arg = OpenStruct(
		debug=False, clean=False, confdir=DEFAULT_CONFDIR,
		mode=0, flags='', targets=[])

#for python3-only versions, this could be replaced with:
#def log(*objects, start='ranger:', sep=' ', end='\n'):
#	print(start, *objects, end=end, sep=sep, file=open(LOGFILE, 'a'))
def log(*objects, **keywords):
	"""
	Writes objects to a logfile (for the purpose of debugging only.)
	Has the same arguments as print() in python3.
	"""
	if LOGFILE is None or arg.clean:
		return
	start = 'start' in keywords and keywords['start'] or 'ranger:'
	sep   =   'sep' in keywords and keywords['sep']   or ' '
	_file =  'file' in keywords and keywords['file']  or open(LOGFILE, 'a')
	end   =   'end' in keywords and keywords['end']   or '\n'
	_file.write(sep.join(map(str, (start, ) + objects)) + end)

def relpath_conf(*paths):
	"""returns the path relative to rangers configuration directory"""
	if arg.clean:
		assert 0, "Should not access relpath_conf in clean mode!"
	else:
		return os.path.join(arg.confdir, *paths)

def relpath(*paths):
	"""returns the path relative to rangers library directory"""
	return os.path.join(RANGERDIR, *paths)
