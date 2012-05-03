# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
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

"""
A console file manager with VI key bindings.

It provides a minimalistic and nice curses interface with a view on the
directory hierarchy.  The secondary task of ranger is to figure out which
program you want to use to open your files with.
"""

import os

# Information
__license__ = 'GPL3'
__version__ = '1.5.4'
__author__ = __maintainer__ = 'Roman Zimbelmann'
__email__ = 'romanz@lavabit.com'

# Constants
RANGERDIR = os.path.dirname(__file__)
TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200
MACRO_DELIMITER = '%'
LOGFILE = '/tmp/ranger_errorlog'
USAGE = '%prog [options] [path/filename]'
STABLE = True

# If the environment variable XDG_CONFIG_HOME is non-empty, CONFDIR is ignored
# and the configuration directory will be $XDG_CONFIG_HOME/ranger instead.
CONFDIR = '~/.config/ranger'

from ranger.core.main import main
