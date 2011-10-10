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

import curses
import os
import pwd
import socket
from os.path import abspath, normpath, join, expanduser, isdir

from ranger.fsobject import Directory
from ranger.ext.keybinding_parser import KeyBuffer, KeyMaps
from ranger.container.history import History
from ranger.ext.signals import SignalDispatcher
from ranger.core.shared import SettingsAware

class Environment(SettingsAware, SignalDispatcher):
	"""
	A collection of data which is relevant for more than one class.
	"""

	cwd = None  # current directory
	copy = None
	cmd = None
	cut = None
	termsize = None
	history = None
	directories = None
	last_search = None
	pathway = None
	path = None

	def __init__(self, path):
		SignalDispatcher.__init__(self)
		self.path = abspath(expanduser(path))
		self._cf = None
		self.pathway = ()
		self.directories = {}
		self.keybuffer = KeyBuffer()
		self.keymaps = KeyMaps(self.keybuffer)
		self.copy = set()
		self.history = History(self.settings.max_history_size, unique=False)

		try:
			self.username = pwd.getpwuid(os.geteuid()).pw_name
		except:
			self.username = 'uid:' + str(os.geteuid())
		self.hostname = socket.gethostname()
		self.home_path = os.path.expanduser('~')

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

	def key_append(self, key):
		"""Append a key to the keybuffer"""

		# special keys:
		if key == curses.KEY_RESIZE:
			self.keybuffer.clear()

		self.keybuffer.add(key)

	def key_clear(self):
		"""Clear the keybuffer"""
		self.keybuffer.clear()

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
				return self.directories[directory.path]
			except AttributeError:
				return None
			except KeyError:
				return directory

	def garbage_collect(self, age, tabs):
		"""Delete unused directory objects"""
		for key in tuple(self.directories):
			value = self.directories[key]
			if age != -1:
				if not value.is_older_than(age) or value in self.pathway:
					continue
				if value in tabs.values():
					continue
			del self.directories[key]
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
			return self.directories[path]
		except KeyError:
			obj = Directory(path)
			self.directories[path] = obj
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
