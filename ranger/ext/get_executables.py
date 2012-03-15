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

from stat import S_IXOTH, S_IFREG
from ranger.ext.iter_tools import unique
from os import listdir, environ, stat


_cached_executables = None


def get_executables():
	"""
	Return all executable files in each of the given directories.

	Looks in $PATH by default.
	"""
	global _cached_executables
	if _cached_executables is None:
		_cached_executables = sorted(get_executables_uncached())
	return _cached_executables


def get_executables_uncached(*paths):
	"""
	Return all executable files in each of the given directories.

	Looks in $PATH by default.
	"""
	if not paths:
		try:
			pathstring = environ['PATH']
		except KeyError:
			return ()
		paths = unique(pathstring.split(':'))

	executables = set()
	for path in paths:
		try:
			content = listdir(path)
		except:
			continue
		for item in content:
			abspath = path + '/' + item
			try:
				filestat = stat(abspath)
			except:
				continue
			if filestat.st_mode & (S_IXOTH | S_IFREG):
				executables.add(item)
	return executables

