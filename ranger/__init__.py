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

# for easier access
from ranger.ext.debug import log, trace

__copyright__ = """
Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
"""

__license__ = 'GPL3'
__version__ = '1.0.3'
__credits__ = 'Roman Zimbelmann'
__author__ = 'Roman Zimbelmann'
__maintainer__ = 'Roman Zimbelmann'
__email__ = 'romanz@lavabit.com'

debug = False

CONFDIR = os.path.expanduser('~/.ranger')
RANGERDIR = os.path.dirname(__file__)

sys.path.append(CONFDIR)

USAGE = '%prog [options] [path/filename]'

from ranger.__main__ import main
