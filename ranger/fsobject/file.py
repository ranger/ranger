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

import re
from ranger.fsobject import FileSystemObject

N_FIRST_BYTES = 256
control_characters = set(chr(n) for n in
		set(range(0, 9)) | set(range(14, 32)))

# Don't even try to preview files which mach this regular expression:
PREVIEW_BLACKLIST = re.compile(r"""
		# look at the extension:
		\.(
			# one character extensions:
				[oa]
			# media formats:
				| avi | mpe?g | mp\d | og[gmv] | wm[av] | mkv | flv
				| vob | wav | mpc | flac | divx? | xcf | pdf
			# binary files:
				| torrent | class | so | img | py[co] | dmg
		)
		# ignore filetype-independent suffixes:
			(\.part|\.bak|~)?
		# ignore fully numerical file extensions:
			(\.\d+)*?
		$
""", re.VERBOSE | re.IGNORECASE)

# Preview these files (almost) always:
PREVIEW_WHITELIST = re.compile(r"""
		\.(
			txt | py | c
		)
		# ignore filetype-independent suffixes:
			(\.part|\.bak|~)?
		$
""", re.VERBOSE | re.IGNORECASE)

class File(FileSystemObject):
	is_file = True
	preview_data = None
	preview_known = False
	preview_loading = False

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

	def has_preview(self):
		if not self.fm.settings.preview_files:
			return False
		if self.is_socket or self.is_fifo or self.is_device:
			return False
		if not self.accessible:
			return False
		if self.fm.settings.preview_script and \
				self.fm.settings.use_preview_script:
			return True
		if self.image or self.container:
			return False
		if PREVIEW_WHITELIST.search(self.basename):
			return True
		if PREVIEW_BLACKLIST.search(self.basename):
			return False
		if self.path == '/dev/core' or self.path == '/proc/kcore':
			return False
		if self.is_binary():
			return False
		return True

	def get_preview_source(self, width, height):
		return self.fm.get_preview(self.realpath, width, height)
