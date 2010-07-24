# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# This software is licensed under the GNU GPLv3; see COPYING for details.
import os.path
from os.path import join, abspath, expanduser, normpath
from pithy.ext.calculate_scroll_pos import calculate_scroll_pos
from pithy.ext.lazy_property import lazy_property
from pithy.ext.permission_string import permission_string
from stat import S_IFIFO, S_IFSOCK, S_IXUSR, S_ISDIR, S_ISLNK

def npath(path, cwd='.'):
	if not path:
		return '/'
	if path[0] == '~':
		return normpath(join(cwd, expanduser(path)))
	return normpath(join(cwd, path))


class BadStat(object):
	st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, \
			st_atime, st_mtime, st_ctime = (0, ) * 10


class File(object):
	def __init__(self, path, parent):
		self.path = path
		self.parent = parent

	@lazy_property
	def extension(self):
		return os.path.splitext(self.basename)[1][1:]

	@lazy_property
	def basename(self):
		return os.path.basename(self.path)

	@lazy_property
	def is_dir(self):
		return S_ISDIR(self.mode)

	@lazy_property
	def is_link(self):
		return S_ISLNK(self.mode)

	@lazy_property
	def stat(self):
		try:
			result = os.lstat(self.path)
		except:
			result = BadStat()
		if S_ISLNK(result.st_mode):
			try:
				result = os.stat(self.path)
				self.is_link = True
			except OSError:
				pass
		else:
			self.is_link = False
		return result

	@lazy_property
	def mode(self):
		return self.stat.st_mode

	@lazy_property
	def permission_string(self):
		return permission_string(self.mode)

	@lazy_property
	def classification(self):
		mode_bits = self.mode & 0o170000
		if self.is_link:
			return '@'
		if self.is_dir:
			return '/'
		if mode_bits == S_IFIFO:
			return '|'
		if mode_bits == S_IFSOCK:
			return '='
		if self.mode & S_IXUSR:
			return '*'
		return ''


class Directory(File):
	_files = None
	pointer = 0
	scroll_begin = 0

	def load(self):
		sort_key = self.status.sort_key
		try: filenames = os.listdir(self.path)
		except: return
		if sort_key is None:
			filenames.sort(key=lambda fname: fname.lower())
		file_filter = self.status.hooks.filter
		files = [File(npath(path, self.path), self) \
				for path in filenames if file_filter(path, self.path)]
		if sort_key is not None:
			files.sort(key=sort_key)
		if self.status.directories_first:
			files.sort(key=lambda f: not f.is_dir)
		self._files = files

	def sync_pointer(self, winsize):
		self.scroll_begin = calculate_scroll_pos(winsize, len(self.files),
				self.pointer, self.scroll_begin)

	def select_filename(self, filename):
		for i, f in enumerate(self.files):
			if f.path == filename:
				self.pointer = i
				break

	@lazy_property
	def files(self):
		self.load()
		return self._files

	@property
	def current_file(self):
		try:
			return self.files[self.pointer]
		except:
			return None
