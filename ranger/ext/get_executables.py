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

import stat
import os
from os.path import isfile, join, exists
from ranger.ext.iter_tools import unique

def get_executables(*paths):
	"""
	Return all executable files in each of the given directories.

	Looks in $PATH by default.
	"""
	if not paths:
		try:
			pathstring = os.environ['PATH']
		except KeyError:
			return ()
		paths = unique(pathstring.split(':'))

	executables = set()
	for path in paths:
		try:
			content = os.listdir(path)
		except:
			continue
		for item in content:
			abspath = join(path, item)
			try:
				filestat = os.stat(abspath)
			except:
				continue
			if filestat.st_mode & (stat.S_IXOTH | stat.S_IFREG):
				executables.add(item)
	return executables
