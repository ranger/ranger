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

from ctypes import CDLL, CFUNCTYPE, c_char_p, c_int, c_uint32
from ctypes.util import find_library
from os import fdopen
from ranger.shared import FileManagerAware

class DirectoryObserver(FileManagerAware):
	"""Uses the Linux inotify subsystem to observe a directory for
	   changes. Requires kernel version 2.6.13 or higher.
	"""

	def __init__(self):
		self.enabled = False
		self.map_watch_to_dir = {}
		self.map_dir_to_watch = {}

		libc_path = find_library('c')
		if libc_path:
			try:
				libc = CDLL(libc_path)
			except:
				pass
			else:
				try:
					init_watch = CFUNCTYPE(c_int)(('inotify_rm_watch', libc))
					self._add_watch = CFUNCTYPE(c_int, c_int, c_char_p, c_uint32)(('inotify_add_watch', libc))
					self._del_watch = CFUNCTYPE(c_int, c_int, c_uint32)(('inotify_rm_watch', libc))
				except:
					pass
				else:
					file_handle = init_watch()
					if file_handle != -1:
						try:
							self.file_handle = fdopen(self.file_handle, 'rb')
						except:
							pass
						else:
							self.fm.wait_handles.append(self.file_handle)

	def add_watch(self, directory):
		""" """
		if self.enabled:
			watch_handle = self._add_watch(self.file_handle, str(directory), 0)
			if watch_handle != -1:
				self.map_watch_to_dir[watch_handle] = directory
				self.map_dir_to_watch[directory] = watch_handle

	def del_watch(self, directory):
		""" """
		if self.enabled and directory in self.map_dir_to_watch:
			watch_handle = self.map_dir_to_watch[directory]
			self._del_watch(self.file_handle, watch_handle)
			del self.map_watch_to_dir[watch_handle]
			del self.map_dir_to_watch[directory]
