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

import os.path
import stat
from stat import S_ISLNK, S_ISDIR
from os import chdir, getcwd, listdir, stat as os_stat, lstat as os_lstat
from os.path import join, isdir, basename
from collections import deque
from time import time

from ranger.ext.mount_path import mount_path
from ranger.fsobject import BAD_INFO, File, FileSystemObject, FileStatus
from ranger.shared import SettingsAware
from ranger.ext.accumulator import Accumulator
import ranger.fsobject

class Directory(FileSystemObject, Accumulator, SettingsAware):
	is_directory = True

	def __init__(self, path, **kw):
		assert not os.path.isfile(path), "No directory given!"

		Accumulator.__init__(self)
		FileSystemObject.__init__(self, path, **kw)

		self.files        = {}
		self.filenames    = []
		self.filestats    = {}
		self.marked_items = set()

		for opt in ('sort_directories_first', 'sort', 'sort_reverse',
				'sort_case_insensitive'):
			self.settings.signal_bind(
				'setopt.' + opt, self.request_resort, weak=True)

		for opt in ('hidden_filter', 'show_hidden'):
			self.settings.signal_bind(
				'setopt.' + opt, self.request_reload, weak=True)

	def get_list(self):
		return self.files

	def mark_item(self, item, val):
		#item._mark(val)
		if val:
			self.marked_items.add(item)
		else:
			self.marked_items.discard(item)

	def toggle_mark(self, item):
		self.mark_item(item, not item.marked)

	def toggle_all_marks(self):
		for item in self.filenames:
			self.toggle_mark(item)

	def mark_all(self, val):
		if val:
			for item in self.files:
				self.mark_item(item, val)
		else:
			self._clear_marked_items()

	def _clear_marked_items(self):
		#for item in self.marked_items:
		#	item._mark(False)
		self.marked_items.clear()

	def get_selection(self):
		"""READ ONLY"""
		return self.marked_items or self.pointed_obj

	def handle_changes(self, events, filename):
		"""Gets called whenever something in a visible dictory changes"""
		if events & 0x00000006: # IN_ATTRIB | IN_MODIFY
			self.files[filename].load()

			if events & 0x00000002: # IN_MODIFY
				pass # FIXME: Update preview panel

		elif events & 0x00000240: # IN_DELETE | IN_MOVED_FROM
			self.filenames.remove(filename)
			del self.filestats[filename]

		elif events & 0x00000180: # IN_CREATE | IN_MOVED_TO
			file_path = self.path + '/' + filename

			if events & 0x40000000: # IN_ISDIR
				self.files[filename] = Directory(file_path, path_is_abs=True)
			else:
				self.files[filename] = File(file_path, path_is_abs=True)

		elif events & 0x00000800: # IN_MOVE_SELF
			self.env.enter_dir('..', history=False)

		elif events & 0x00002400: # IN_DELETE_SELF | IN_UNMOUNT
			self.env.directory_queue.remove(self.path)
			del self.env.directories[self.path]
			self.env.enter_dir('..', history=False)

	def move_to_obj(self, arg):
		try:
			arg = arg.path
		except:
			pass
		self.load_content_once(schedule=False)
		if self.empty():
			return

		Accumulator.move_to_obj(self, arg, attr='path')

	def search_fnc(self, fnc, forward=True):
		if not hasattr(fnc, '__call__'):
			return False

		direction = forward and 1 or -1
		for slice_index, slice in enumerate(
				(self.filenames[self.pointer+direction::direction],
				 self.filenames[          :self.pointer:direction])):
			for file_index, name in enumerate(slice):
				if fnc(name):
					if slice_index == 0:
						self.pointer += direction * file_index + direction
					else:
						if forward:
							self.pointer = file_index
						else:
							self.pointer = len(self.filenames) - file_index - 1
					#self.pointed_obj =
					return True
		return False

	def set_cycle_list(self, lst):
		self.cycle_list = deque(lst)

	def cycle(self, forward=True):
		if self.cycle_list:
			if forward is True:
				self.cycle_list.rotate(-1)
			elif forward is False:
				self.cycle_list.rotate(1)

			self.move_to_obj(self.cycle_list[0])

	def get_description(self):
		return "Loading " + str(self)

	def go(self):
		"""enter the directory if the filemanager is running"""
		if self.fm:
			return self.fm.enter_dir(self.path)
		return False

	def empty(self):
		"""Is the directory empty?"""
		return self.filenames and True or False

	def __nonzero__(self):
		"""Always True"""
		return True
	__bool__ = __nonzero__

	def __len__(self):
		"""The number of containing files"""
		assert self.accessible
		assert self.content_loaded
		assert self.filenames is not None
		return len(self.filenames)

	def __eq__(self, other):
		"""Check for equality of the directories paths"""
		return isinstance(other, Directory) and self.path == other.path

	def __neq__(self, other):
		"""Check for inequality of the directories paths"""
		return not self.__eq__(other)

	def __hash__(self):
		return hash(self.path)

	def load(self):
		"""
		Loads and sorts the contents of a directory without creating
		the corresponding FileSystemObjects yet.
		"""
		self.change_load_procedure()
		self.load()

	def change_load_procedure(self):
		"""Replaces the load method with generated optimized code"""
		options = {}

		global_filter = self.settings.hidden_filter
		if self.settings.show_hidden or not (global_filter or self.filter):
			options['filter_code'] = "files = listdir('.')"
		else:
			options['filter_code'] = "global_filter = self.settings.hidden_filter"

			if hasattr(global_filter, 'search'):
				options['filter_code']  += ".search"
				options['global_filter'] = "global_filter(name)"
			elif global_filter:
				options['global_filter'] = "name in global_filter"
			else:
				options['global_filter'] = ""

			if self.filter:
				if options['global_filter']:
					options['local_filter'] += "or name in local_filter"
				else:
					options['local_filter'] += "name in local_filter"
			else:
				options['local_filter'] = ""

			options['filter_code'] += (
				"\n	files = "
				"[name for name in listdir('.') "
				"if not ({global_filter}{local_filter})]".format(**options) )

		if self.settings.sort_reverse:
			options['sorter_byte'] = "\xFF"
			options['do_reverse']  = True
		else:
			options['sorter_byte'] = "\x01"
			options['do_reverse']  = False

		if self.settings.sort_case_insensitive:
			options['case_method'] = ".lower()"
		else:
			options['case_method'] = ""

		if self.settings.sort_directories_first:
			options['key_sorter'] = (
				", key=lambda name: (stats[name].st_mode & 0o170000 == 0o040000) "
				"and ('{sorter_byte}' + name{case_method}) or (name{case_method})"
				.format(**options) )
		else:
			if self.settings.sort_case_insensitive:
				options['key_sorter'] = ", key=str.lower"
			else:
				options['key_sorter'] = ""

		loader_source = (
			"def load(self):"
		   "\n	previous_path = getcwd()"
			"\n	chdir(self.path)"
			"\n	{filter_code}"
			"\n"
			"\n	stats = {{}}"
			"\n	for name in files:"
			"\n		stats[name] = os_lstat(name)"
			"\n"
			"\n	files.sort(reverse={do_reverse}{key_sorter})"
			"\n	self.filenames = files"
			"\n	self.filestats = stats"
		   "\n	chdir(previous_path)"
		).format(**options)

		exec( compile(loader_source, 'directory.py:generated_loader', 'exec') )
		Directory.load = load
