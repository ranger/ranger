# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

import os
from os.path import abspath, normpath, join, expanduser, isdir

from ranger.fsobject import Directory
from ranger.container.history import History
from ranger.ext.signals import SignalDispatcher
from ranger.core.shared import SettingsAware, FileManagerAware

# COMPAT
class EnvironmentCompatibilityWrapper(object):
	def _get_copy(self): return self.fm.copy_buffer
	def _set_copy(self, obj): self.fm.copy_buffer = obj
	copy = property(_get_copy, _set_copy)

	def _get_cut(self): return self.fm.do_cut
	def _set_cut(self, obj): self.fm.do_cut = obj
	cut = property(_get_cut, _set_cut)

	def _get_keymaps(self): return self.fm.ui.keymaps
	def _set_keymaps(self, obj): self.fm.ui.keymaps = obj
	keymaps = property(_get_keymaps, _set_keymaps)

	def _get_keybuffer(self): return self.fm.ui.keybuffer
	def _set_keybuffer(self, obj): self.fm.ui.keybuffer = obj
	keybuffer = property(_get_keybuffer, _set_keybuffer)

	def _get_username(self): return self.fm.username
	def _set_username(self, obj): self.fm.username = obj
	username = property(_get_username, _set_username)

	def _get_hostname(self): return self.fm.hostname
	def _set_hostname(self, obj): self.fm.hostname = obj
	hostname = property(_get_hostname, _set_hostname)

	def _get_home_path(self): return self.fm.home_path
	def _set_home_path(self, obj): self.fm.home_path = obj
	home_path = property(_get_home_path, _set_home_path)

class Environment(SettingsAware, FileManagerAware, SignalDispatcher,
		EnvironmentCompatibilityWrapper):
	"""
	A collection of data which is relevant for more than one class.
	"""

	def __init__(self, path):
		SignalDispatcher.__init__(self)
		self.cwd = None  # Current Working Directory
		self._cf = None  # Current File
		self.history = History(self.settings.max_history_size, unique=False)
		self.last_search = None
		self.path = abspath(expanduser(path))
		self.pathway = ()
		self.signal_bind('move', self._set_cf_from_signal, priority=0.1,
				weak=True)

	def _set_cf_from_signal(self, signal):
		self._cf = signal.new

	def _set_cf(self, value):
		if value is not self._cf:
			previous = self._cf
			self.signal_emit('move', previous=previous, new=value)

	def _get_cf(self):
		return self._cf

	cf = property(_get_cf, _set_cf)

	def at_level(self, level):
		"""
		Returns the FileSystemObject at the given level.
		level >0 => previews
		level 0 => current file/directory
		level <0 => parent directories
		"""
		if level <= 0:
			try:
				return self.pathway[level - 1]
			except IndexError:
				return None
		else:
			directory = self.cf
			for i in range(level - 1):
				if directory is None:
					return None
				if directory.is_directory:
					directory = directory.pointed_obj
				else:
					return None
			try:
				return self.fm.directories[directory.path]
			except AttributeError:
				return None
			except KeyError:
				return directory

	def garbage_collect(self, age, tabs):
		"""Delete unused directory objects"""
		for key in tuple(self.fm.directories):
			value = self.fm.directories[key]
			if age != -1:
				if not value.is_older_than(age) or value in self.pathway:
					continue
				if value in tabs.values():
					continue
			del self.fm.directories[key]
			if value.is_directory:
				value.files = None
		self.settings.signal_garbage_collect()
		self.signal_garbage_collect()

	def get_selection(self):
		if self.cwd:
			return self.cwd.get_selection()
		return set()

	def get_directory(self, path):
		"""Get the directory object at the given path"""
		path = abspath(path)
		try:
			return self.fm.directories[path]
		except KeyError:
			obj = Directory(path)
			self.fm.directories[path] = obj
			return obj

	def get_free_space(self, path):
		stat = os.statvfs(path)
		return stat.f_bavail * stat.f_bsize

	def assign_cursor_positions_for_subdirs(self):
		"""Assign correct cursor positions for subdirectories"""
		last_path = None
		for path in reversed(self.pathway):
			if last_path is None:
				last_path = path
				continue

			path.move_to_obj(last_path)
			last_path = path

	def ensure_correct_pointer(self):
		if self.cwd:
			self.cwd.correct_pointer()

	def history_go(self, relative):
		"""Move relative in history"""
		if self.history:
			self.history.move(relative).go(history=False)

	def enter_dir(self, path, history = True):
		"""Enter given path"""
		if path is None: return
		path = str(path)

		previous = self.cwd

		# get the absolute path
		path = normpath(join(self.path, expanduser(path)))

		if not isdir(path):
			return False
		new_cwd = self.get_directory(path)

		try:
			os.chdir(path)
		except:
			return True
		self.path = path
		self.cwd = new_cwd

		self.cwd.load_content_if_outdated()

		# build the pathway, a tuple of directory objects which lie
		# on the path to the current directory.
		if path == '/':
			self.pathway = (self.get_directory('/'), )
		else:
			pathway = []
			currentpath = '/'
			for dir in path.split('/'):
				currentpath = join(currentpath, dir)
				pathway.append(self.get_directory(currentpath))
			self.pathway = tuple(pathway)

		self.assign_cursor_positions_for_subdirs()

		# set the current file.
		self.cwd.sort_directories_first = self.settings.sort_directories_first
		self.cwd.sort_reverse = self.settings.sort_reverse
		self.cwd.sort_if_outdated()
		self.cf = self.cwd.pointed_obj

		if history:
			self.history.add(new_cwd)

		self.signal_emit('cd', previous=previous, new=self.cwd)

		return True
