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

control_characters = set(chr(n) for n in set(range(0, 9)) | set(range(14,32)))
N_FIRST_BYTES = 20

from .fsobject import FileSystemObject as SuperClass
class File(SuperClass):
	is_file = True

	@property
	def firstbytes(self):
		try:
			return self._firstbytes
		except:
			try:
				f = open(self.path, 'r')
				self._firstbytes = f.read(N_FIRST_BYTES)
				f.close()
				return self._firstbytes
			except:
				pass

	def is_binary(self):
		if self.firstbytes and control_characters & set(self.firstbytes):
			return True
		return False

