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

CONTAINER_EXTENSIONS = 'rar zip tar gz bz bz2 tgz 7z iso cab'.split()

from os import access, listdir, lstat, readlink, stat
from time import time
from os.path import abspath, basename, dirname, realpath
from . import BAD_INFO
from ranger.shared import MimeTypeAware, FileManagerAware
from ranger.ext.shell_escape import shell_escape
from ranger.ext.spawn import spawn
from ranger.ext.human_readable import human_readable

class FileSystemObject(MimeTypeAware, FileManagerAware):
	(_filetype,
	_shell_escaped_basename,
	basename,
	basename_lower,
	dirname,
	extension,
	infostring,
	last_used,
	path,
	permissions,
	readlink,
	stat) = (None,) * 12

	(content_loaded,
	force_load,

	is_device,
	is_directory,
	is_file,
	is_fifo,
	is_link,
	is_socket,

	accessible,
	exists,
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

	mimetype_tuple = ()
	size = 0


	def __init__(self, path, preload=None, path_is_abs=False):
		MimeTypeAware.__init__(self)

		if not path_is_abs:
			path = abspath(path)
		self.path = path
		self.basename = basename(path)
		self.basename_lower = self.basename.lower()
		self.dirname = dirname(path)
		self.realpath = self.path
		self.preload = preload

		try:
			lastdot = self.basename.rindex('.') + 1
			self.extension = self.basename[lastdot:].lower()
		except ValueError:
			self.extension = None

		self.use()

	def __repr__(self):
		return "<{0} {1}>".format(self.__class__.__name__, self.path)

	@property
	def shell_escaped_basename(self):
		if self._shell_escaped_basename is None:
			self._shell_escaped_basename = shell_escape(self.basename)
		return self._shell_escaped_basename

	@property
	def filetype(self):
		if self._filetype is None:
			try:
				got = spawn(["file", '-Lb', '--mime-type', self.path])
			except OSError:
				self._filetype = ''
			else:
				self._filetype = got
		return self._filetype

	def get_description(self):
		return "Loading " + str(self)

	def __str__(self):
		"""returns a string containing the absolute path"""
		return str(self.path)

	def use(self):
		"""mark the filesystem-object as used at the current time"""
		self.last_used = time()

	def is_older_than(self, seconds):
		"""returns whether this object wasn't use()d in the last n seconds"""
		if seconds < 0:
			return True
		return self.last_used + seconds < time()

	def set_mimetype(self):
		"""assign attributes such as self.video according to the mimetype"""
		self._mimetype = self.mimetypes.guess_type(self.basename, False)[0]
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

	def load(self):
		"""
		reads useful information about the filesystem-object from the
		filesystem and caches it for later use
		"""

		self.loaded = True

		# Get the stat object, either from preload or from [l]stat
		new_stat = None
		path = self.path
		if self.preload:
			new_stat = self.preload[1]
			is_link = (new_stat.st_mode & 0o120000) == 0o120000
			if is_link:
				new_stat = self.preload[0]
			self.preload = None
		else:
			try:
				new_stat = lstat(path)
				is_link = (new_stat.st_mode & 0o120000) == 0o120000
				if is_link:
					new_stat = stat(path)
			except:
				pass

		# Set some attributes
		if new_stat:
			mode = new_stat.st_mode
			self.accessible = True
			self.is_device = (mode & 0o060000) == 0o060000
			self.is_fifo = (mode & 0o010000) == 0o010000
			self.is_link = is_link
			self.is_socket = (mode & 0o140000) == 0o140000
			if access(path, 0):
				self.exists = True
				if self.is_directory:
					self.runnable = (mode & 0o0100) == 0o0100
			else:
				self.exists = False
				self.runnable = False
			if is_link:
				self.realpath = realpath(path)
				self.readlink = readlink(path)
		else:
			self.accessible = False

		# Determine infostring
		if self.is_file:
			if new_stat:
				self.size = new_stat.st_size
				self.infostring = ' ' + human_readable(self.size)
			else:
				self.size = 0
				self.infostring = '?'
		elif self.is_directory:
			try:
				self.size = len(listdir(path))  # bite me
			except OSError:
				self.size = 0
				self.infostring = '?'
				self.accessible = False
			else:
				self.infostring = ' %d' % self.size
				self.accessible = True
				self.runnable = True
		elif self.is_device:
			self.size = 0
			self.infostring = 'dev'
		elif self.is_fifo:
			self.size = 0
			self.infostring = 'fifo'
		elif self.is_socket:
			self.size = 0
			self.infostring = 'sock'
		if self.is_link:
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

	def go(self):
		"""enter the directory if the filemanager is running"""
		if self.fm:
			return self.fm.enter_dir(self.path)
		return False

	def load_if_outdated(self):
		"""
		Calls load() if the currently cached information is outdated
		or nonexistant.
		"""
		if not self.loaded:
			self.load()
			return True
		try:
			real_mtime = lstat(self.path).st_mtime
		except OSError:
			real_mtime = None
		if self.stat:
			cached_mtime = self.stat.st_mtime
		else:
			cached_mtime = 0
		if real_mtime != cached_mtime:
			self.load()
			return True
		return False
