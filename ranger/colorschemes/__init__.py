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

"""Colorschemes are required to be located here,
or in the CONFDIR/colorschemes/ directory"""
import sys
import ranger
from ranger.ext.get_all_modules import get_all_modules
from os.path import expanduser, dirname, exists, join

__all__ = get_all_modules(dirname(__file__))

from ranger.colorschemes import *
from ranger.ext.relpath import relpath_conf

if exists(relpath_conf('colorschemes')):
	initpy = relpath_conf('colorschemes/__init__.py')
	if not exists(initpy):
		open(initpy, 'w').write("""# Automatically generated:
from ranger.ext.get_all_modules import get_all_modules
from os.path import dirname

__all__ = get_all_modules(dirname(__file__))
""")

	try:
		import sys
		sys.path[0:0] = [ranger.CONFDIR]
		from colorschemes import *
	except ImportError:
		pass

