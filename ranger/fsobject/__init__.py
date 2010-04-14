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

"""FileSystemObjects are representation of files and directories
with fast access to their properties through caching"""

T_FILE = 'file'
T_DIRECTORY = 'directory'
T_UNKNOWN = 'unknown'
T_NONEXISTANT = 'nonexistant'

BAD_INFO = '?'

class NotLoadedYet(Exception):
	pass

from .fsobject import FileSystemObject
from .file import File
from .directory import Directory, NoDirectoryGiven
from .loader import Loader
