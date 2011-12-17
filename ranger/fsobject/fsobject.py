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

CONTAINER_EXTENSIONS = ('7z', 'ace', 'ar', 'arc', 'bz', 'bz2', 'cab', 'cpio',
	'cpt', 'deb', 'dgc', 'dmg', 'gz', 'iso', 'jar', 'msi', 'pkg', 'rar',
	'shar', 'tar', 'tbz', 'tgz', 'xar', 'xpi', 'xz', 'zip')

import re
from os import lstat, stat
from os.path import abspath, basename, dirname, realpath, splitext, extsep
from ranger.core.shared import FileManagerAware
from ranger.ext.shell_escape import shell_escape
from ranger.ext.spawn import spawn
from ranger.ext.lazy_property import lazy_property
from ranger.ext.human_readable import human_readable

if hasattr(str, 'maketrans'):
	maketrans = str.maketrans
else:
	from string import maketrans
_unsafe_chars = '\n' + ''.join(map(chr, range(32))) + ''.join(map(chr, range(128, 256)))
_safe_string_table = maketrans(_unsafe_chars, '?' * len(_unsafe_chars))
_extract_number_re = re.compile(r'([^0-9]?)(\d*)')

def safe_path(path):
	return path.translate(_safe_string_table)

class FileSystemObject(FileManagerAware):
	(basename,
	basename_lower,
	dirname,
	extension,
	infostring,
	path,
	permissions,
	stat) = (None,) * 8

	(content_loaded,
	force_load,

	is_device,
	is_directory,
	is_file,
	is_fifo,
	is_link,
	is_socket,

	accessible,
	exists,       # "exists" currently means "link_target_exists"
	loaded,
	marked,
	runnable,
	stopped,
	tagged,

	audio,
	container,
	document,
	image,
	media,
	video) = (False,) * 21

	size = 0


	def __init__(self, path, preload=None, path_is_abs=False):
		if not path_is_abs:
			path = abspath(path)
		self.path = path
		self.basename = basename(path)
		self.basename_lower = self.basename.lower()
		self.extension = splitext(self.basename)[1].lstrip(extsep) or None
		self.dirname = dirname(path)
		self.preload = preload

		try:
			lastdot = self.basename.rindex('.') + 1
			self.extension = self.basename[lastdot:].lower()
		except ValueError:
			self.extension = None

	def __repr__(self):
		return "<{0} {1}>".format(self.__class__.__name__, self.path)

	@lazy_property
	def shell_escaped_basename(self):
		return shell_escape(self.basename)

	@lazy_property
	def filetype(self):
		try:
			return spawn(["file", '-Lb', '--mime-type', self.path])
		except OSError:
			return ""

	@lazy_property
	def basename_natural(self):
		return [c if i % 3 == 1 else (int(c) if c else 0) for i, c in \
			enumerate(_extract_number_re.split(self.basename))]

	@lazy_property
	def basename_natural_lower(self):
		return [c if i % 3 == 1 else (int(c) if c else 0) for i, c in \
			enumerate(_extract_number_re.split(self.basename_lower))]

	@lazy_property
	def safe_basename(self):
		return self.basename.translate(_safe_string_table)


	for attr in ('video', 'audio', 'image', 'media', 'document', 'container'):
		exec("%s = lazy_property("
			"lambda self: self.set_mimetype() or self.%s)" % (attr, attr))

	def __str__(self):
		"""returns a string containing the absolute path"""
		return str(self.path)

	def use(self):
		"""Used in garbage-collecting.  Override in Directory"""

	def look_up_cumulative_size(self):
		pass # normal files have no cumulative size

	def set_mimetype(self):
		"""assign attributes such as self.video according to the mimetype"""
		basename = self.basename
		if self.extension == 'part':
			basename = basename[0:-5]
		self._mimetype = self.fm.mimetypes.guess_type(basename, False)[0]
		if self._mimetype is None:
			self._mimetype = ''

		self.video = self._mimetype.startswith('video')
		self.image = self._mimetype.startswith('image')
		self.audio = self._mimetype.startswith('audio')
		self.media = self.video or self.image or self.audio
		self.document = self._mimetype.startswith('text')
		self.container = self.extension in CONTAINER_EXTENSIONS

		keys = ('video', 'audio', 'image', 'media', 'document', 'container')
		self._mimetype_tuple = tuple(key for key in keys if getattr(self, key))

		if self._mimetype == '':
			self._mimetype = None

	@property
	def mimetype(self):
		try:
			return self._mimetype
		except:
			self.set_mimetype()
			return self._mimetype

	@property
	def mimetype_tuple(self):
		try:
			return self._mimetype_tuple
		except:
			self.set_mimetype()
			return self._mimetype_tuple

	def mark(self, boolean):
		directory = self.env.get_directory(self.dirname)
		directory.mark_item(self)

	def _mark(self, boolean):
		"""Called by directory.mark_item() and similar functions"""
		self.marked = bool(boolean)

	@lazy_property
	def realpath(self):
		if self.is_link:
			try:
				return realpath(self.path)
			except:
				return None  # it is impossible to get the link destination
		return self.path

	def load(self):
		"""
		reads useful information about the filesystem-object from the
		filesystem and caches it for later use
		"""

		self.fm.update_preview(self.path)
		self.loaded = True

		# Get the stat object, either from preload or from [l]stat
		self.permissions = None
		new_stat = None
		path = self.path
		is_link = False
		if self.preload:
			new_stat = self.preload[1]
			is_link = new_stat.st_mode & 0o170000 == 0o120000
			if is_link:
				new_stat = self.preload[0]
			self.preload = None
			self.exists = True if new_stat else False
		else:
			try:
				new_stat = lstat(path)
				is_link = new_stat.st_mode & 0o170000 == 0o120000
				if is_link:
					new_stat = stat(path)
				self.exists = True
			except:
				self.exists = False

		# Set some attributes

		self.accessible = True if new_stat else False
		mode = new_stat.st_mode if new_stat else 0

		format = mode & 0o170000
		if format == 0o020000 or format == 0o060000:  # stat.S_IFCHR/BLK
			self.is_device = True
			self.size = 0
			self.infostring = 'dev'
		elif format == 0o010000:  # stat.S_IFIFO
			self.is_fifo = True
			self.size = 0
			self.infostring = 'fifo'
		elif format == 0o140000:  # stat.S_IFSOCK
			self.is_socket = True
			self.size = 0
			self.infostring = 'sock'
		elif self.is_file:
			if new_stat:
				self.size = new_stat.st_size
				self.infostring = ' ' + human_readable(self.size)
			else:
				self.size = 0
				self.infostring = '?'
		if is_link:
			self.is_link = True
			if not self.is_directory:
				self.infostring = '->' + self.infostring

		self.stat = new_stat

	def get_permission_string(self):
		if self.permissions is not None:
			return self.permissions

		if self.is_directory:
			perms = ['d']
		elif self.is_link:
			perms = ['l']
		else:
			perms = ['-']

		mode = self.stat.st_mode
		test = 0o0400
		while test:  # will run 3 times because 0o400 >> 9 = 0
			for what in "rwx":
				if mode & test:
					perms.append(what)
				else:
					perms.append('-')
				test >>= 1

		self.permissions = ''.join(perms)
		return self.permissions

	def load_if_outdated(self):
		"""
		Calls load() if the currently cached information is outdated
		or nonexistant.
		"""
		if not self.loaded:
			self.load()
			return True
		try:
			real_ctime = lstat(self.path).st_ctime
		except OSError:
			real_ctime = None
		if not self.stat or self.stat.st_ctime != real_ctime:
			self.load()
			return True
		return False
