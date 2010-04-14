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
DOCUMENT_EXTENSIONS = 'pdf doc ppt odt'.split()
DOCUMENT_BASENAMES = 'README TODO LICENSE COPYING INSTALL'.split()

import stat
import os
from time import time
from subprocess import Popen, PIPE
from os.path import abspath, basename, dirname, realpath
from . import T_FILE, T_DIRECTORY, T_UNKNOWN, T_NONEXISTANT, BAD_INFO
from ranger.shared import MimeTypeAware, FileManagerAware
from ranger.ext.shell_escape import shell_escape
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
	type = T_UNKNOWN
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

	def __init__(self, path):
		MimeTypeAware.__init__(self)

		path = abspath(path)
		self.path = path
		self.basename = basename(path)
		self.basename_lower = self.basename.lower()
		self.dirname = dirname(path)
		self.realpath = realpath(path)

		try:
			lastdot = self.basename.rindex('.') + 1
			self.extension = self.basename[lastdot:].lower()
		except ValueError:
			self.extension = None

		self.set_mimetype()
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
				got = Popen(["file", '-Lb', '--mime-type', self.path],
						stdout=PIPE).communicate()[0]
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
		self.mimetype = self.mimetypes.guess_type(self.basename, False)[0]
		if self.mimetype is None:
			self.mimetype = ''

		self.video = self.mimetype.startswith('video')
		self.image = self.mimetype.startswith('image')
		self.audio = self.mimetype.startswith('audio')
		self.media = self.video or self.image or self.audio
		self.document = self.mimetype.startswith('text') \
				or (self.extension in DOCUMENT_EXTENSIONS) \
				or (self.basename in DOCUMENT_BASENAMES)
		self.container = self.extension in CONTAINER_EXTENSIONS

		keys = ('video', 'audio', 'image', 'media', 'document', 'container')
		self.mimetype_tuple = tuple(key for key in keys if getattr(self, key))

		if self.mimetype == '':
			self.mimetype = None

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

		try:
			self.stat = os.lstat(self.path)
		except OSError:
			self.stat = None
			self.is_link = False
			self.accessible = False
		else:
			self.is_link = stat.S_ISLNK(self.stat.st_mode)
			if self.is_link:
				try: # try to resolve the link
					self.stat = os.stat(self.path)
				except:  # it failed, so it must be a broken link
					pass
			mode = self.stat.st_mode
			self.is_device = bool(stat.S_ISCHR(mode) or stat.S_ISBLK(mode))
			self.is_socket = bool(stat.S_ISSOCK(mode))
			self.is_fifo = bool(stat.S_ISFIFO(mode))
			self.accessible = True

		if self.accessible and os.access(self.path, os.F_OK):
			self.exists = True
			self.accessible = True

			if os.path.isdir(self.path):
				self.type = T_DIRECTORY
				try:
					self.size = len(os.listdir(self.path))
					self.infostring = ' %d' % self.size
					self.runnable = True
				except OSError:
					self.infostring = BAD_INFO
					self.runnable = False
					self.accessible = False
			elif os.path.isfile(self.path):
				self.type = T_FILE
				self.size = self.stat.st_size
				self.infostring = ' ' + human_readable(self.stat.st_size)
			else:
				self.type = T_UNKNOWN
				if self.is_device:
					self.infostring = 'dev'
				elif self.is_fifo:
					self.infostring = 'fifo'
				elif self.is_socket:
					self.infostring = 'sock'
				else:
					self.infostring = None

		else:
			if self.is_link:
				self.infostring = '->'
			else:
				self.infostring = None
			self.type = T_NONEXISTANT
			self.exists = False
			self.runnable = False

		if self.is_link:
			self.readlink = os.readlink(self.path)

	def get_permission_string(self):
		if self.permissions is not None:
			return self.permissions

		try:
			mode = self.stat.st_mode
		except:
			return '----??----'

		if stat.S_ISDIR(mode):
			perms = ['d']
		elif stat.S_ISLNK(mode):
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
