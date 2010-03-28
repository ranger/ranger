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

from .fsobject import FileSystemObject as SuperClass
class File(SuperClass):
	is_file = True

	@property
	def first4bytes(self):
		try:
			return self._first4bytes
		except:
			try:
				f = open(self.path, 'r')
				self._first4bytes = f.read(4)
				f.close()
				return self._first4bytes
			except:
				pass

	def is_binary(self):
		if not self.first4bytes:
			return
		if self.first4bytes == "\x7F\x45\x4C\x46":
			return True
		if control_characters & set(self.first4bytes):
			return True
		return False

