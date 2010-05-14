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

import stat
import os
from stat import S_ISLNK, S_ISCHR, S_ISBLK, S_ISSOCK, S_ISFIFO, \
		S_ISDIR, S_IXUSR
from time import time
from os.path import abspath, basename, dirname, realpath
from . import BAD_INFO
from ranger.shared import MimeTypeAware, FileManagerAware
from ranger.ext.shell_escape import shell_escape
from ranger.ext.spawn import spawn
from ranger.ext.human_readable import human_readable

class FileSystemObject(MimeTypeAware, FileManagerAware):
	is_file = False
	is_directory = False
	content_loaded = False
	force_load = False
	path = None
	basename = None
	basename_lower = None
	_shell_escaped_basename = None
	_filetype = None
	dirname = None
	extension = None
	exists = False
	accessible = False
	marked = False
	tagged = False
	loaded = False
	runnable = False
	is_link = False
	is_device = False
	is_socket = False
	is_fifo = False
	readlink = None
	stat = None
	infostring = None
	permissions = None
	size = 0

	last_used = None

	stopped = False

	video = False
	image = False
	audio = False
	media = False
	document = False
	container = False
	mimetype_tuple = ()

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

	def determine_infostring(self):
		self.size = 0
		if self.is_device:
			self.infostring = 'dev'
		elif self.is_fifo:
			self.infostring = 'fifo'
		elif self.is_socket:
			self.infostring = 'sock'
		elif self.is_directory:
			try:
				self.size = len(os.listdir(self.path))  # bite me
			except OSError:
				self.infostring = BAD_INFO
				self.accessible = False
			else:
				self.infostring = ' %d' % self.size
				self.accessible = True
				self.runnable = True
		elif self.is_file:
			if self.stat:
				self.size = self.stat.st_size
				self.infostring = ' ' + human_readable(self.size)
			else:
				self.infostring = BAD_INFO
		if self.is_link:
			self.infostring = '->' + self.infostring

	def load(self):
		"""
		reads useful information about the filesystem-object from the
		filesystem and caches it for later use
		"""

		self.loaded = True

		# Get the stat object, either from preload or from os.[l]stat
		self.stat = None
		if self.preload:
			self.stat = self.preload[1]
			self.is_link = S_ISLNK(self.stat.st_mode)
			if self.is_link:
				self.stat = self.preload[0]
			self.preload = None
		else:
			try:
				self.stat = os.lstat(self.path)
			except:
				pass
			else:
				self.is_link = S_ISLNK(self.stat.st_mode)
				if self.is_link:
					try:
						self.stat = os.stat(self.path)
					except:
						pass

		# Set some attributes
		if self.stat:
			mode = self.stat.st_mode
			self.is_device = bool(S_ISCHR(mode) or S_ISBLK(mode))
			self.is_socket = bool(S_ISSOCK(mode))
			self.is_fifo = bool(S_ISFIFO(mode))
			self.accessible = True
			if os.access(self.path, os.F_OK):
				self.exists = True
				if S_ISDIR(mode):
					self.runnable = bool(mode & S_IXUSR)
			else:
				self.exists = False
				self.runnable = False
			if self.is_link:
				self.realpath = realpath(self.path)
				self.readlink = os.readlink(self.path)
		else:
			self.accessible = False

		self.determine_infostring()

	def get_permission_string(self):
		if self.permissions is not None:
			return self.permissions

		try:
			mode = self.stat.st_mode
		except:
			return '----??----'

		if S_ISDIR(mode):
			perms = ['d']
		elif S_ISLNK(mode):
			perms = ['l']
		else:
			perms = ['-']

		for who in ("USR", "GRP", "OTH"):
			for what in "RWX":
				if mode & getattr(stat, "S_I" + what + who):
					perms.append(what.lower())
				else:
					perms.append('-')

		self.permissions = ''.join(perms)
		return self.permissions

	def load_once(self):
		"""calls load() if it has not been called at least once yet"""
		if not self.loaded:
			self.load()
			return True
		return False

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
		if self.load_once():
			return True
		try:
			real_mtime = os.lstat(self.path).st_mtime
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
