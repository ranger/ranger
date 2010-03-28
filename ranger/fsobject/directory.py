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

import os
from collections import deque
from time import time

from ranger import log
from ranger.fsobject import BAD_INFO, File, FileSystemObject
from ranger.shared import SettingsAware
from ranger.ext.accumulator import Accumulator
import ranger.fsobject

def sort_by_basename(path):
	"""returns path.basename (for sorting)"""
	return path.basename

def sort_by_basename_icase(path):
	"""returns case-insensitive path.basename (for sorting)"""
	return path.basename_lower

def sort_by_directory(path):
	"""returns 0 if path is a directory, otherwise 1 (for sorting)"""
	return 1 - path.is_directory

class NoDirectoryGiven(Exception):
	pass

class Directory(FileSystemObject, Accumulator, SettingsAware):
	is_directory = True
	enterable = False
	load_generator = None
	cycle_list = None
	loading = False

	filenames = None
	files = None
	filter = None
	marked_items = None
	scroll_begin = 0
	scroll_offset = 0

	mount_path = '/'
	disk_usage = 0

	last_update_time = -1
	load_content_mtime = -1

	old_show_hidden = None
	old_sort_directories_first = None
	old_sort_reverse = None
	old_sort = None
	old_filter = None
	old_hidden_filter = None

	sort_dict = {
		'basename': sort_by_basename,
		'size': lambda path: path.size,
		'mtime': lambda path: -(path.stat and path.stat.st_mtime or 1),
		'type': lambda path: path.mimetype,
	}

	def __init__(self, path):
		from os.path import isfile

		if isfile(path):
			raise NoDirectoryGiven()

		Accumulator.__init__(self)
		FileSystemObject.__init__(self, path)

		self.marked_items = list()

		# to find out if something has changed:
		self.old_show_hidden = self.settings.show_hidden
		self.old_sort_directories_first = self.settings.sort_directories_first
		self.old_sort = self.settings.sort
		self.old_filter = self.filter
		self.old_hidden_filter = self.settings.hidden_filter
		self.old_sort_reverse = self.settings.sort_reverse
		self.old_sort_case_insensitive = self.settings.sort_case_insensitive

	def get_list(self):
		return self.files

	def mark_item(self, item, val):
		item._mark(val)
		if val:
			if item in self.files and not item in self.marked_items:
				self.marked_items.append(item)
		else:
			while True:
				try:
					self.marked_items.remove(item)
				except ValueError:
					break

	def toggle_mark(self, item):
		self.mark_item(item, not item.marked)

	def toggle_all_marks(self):
		for item in self.files:
			self.toggle_mark(item)

	def mark_all(self, val):
		for item in self.files:
			self.mark_item(item, val)

		if not val:
			del self.marked_items[:]
			self._clear_marked_items()

	def _gc_marked_items(self):
		for item in list(self.marked_items):
			if item.path not in self.filenames:
				self.marked_items.remove(item)

	def _clear_marked_items(self):
		for item in self.marked_items:
			item._mark(False)
		del self.marked_items[:]

	def get_selection(self):
		"""READ ONLY"""
		self._gc_marked_items()
		if self.marked_items:
			return [item for item in self.files if item.marked]
		elif self.pointed_obj:
			return [self.pointed_obj]
		else:
			return []

	def load_bit_by_bit(self):
		"""
		Returns a generator which load a part of the directory
		in each iteration.
		"""

		# log("generating loader for " + self.path + "(" + str(id(self)) + ")")
		from os.path import join, isdir, basename
		from os import listdir
		import ranger.ext.mount_path

		self.loading = True
		self.load_if_outdated()

		try:
			if self.exists and self.runnable:
				yield
				self.mount_path = ranger.ext.mount_path.mount_path(self.path)

				filenames = []
				for fname in listdir(self.path):
					if not self.settings.show_hidden:
						hfilter = self.settings.hidden_filter
						if hfilter:
							if isinstance(hfilter, str) and hfilter in fname:
								continue
							if hasattr(hfilter, 'search') and \
								hfilter.search(fname):
								continue
					if isinstance(self.filter, str) and self.filter \
							and self.filter not in fname:
						continue
					filenames.append(join(self.path, fname))
				yield

				self.load_content_mtime = os.stat(self.path).st_mtime

				marked_paths = [obj.path for obj in self.marked_items]

				files = []
				for name in filenames:
					if isdir(name):
						try:
							item = self.fm.env.get_directory(name)
						except:
							item = Directory(name)
					else:
						item = File(name)
					item.load_if_outdated()
					files.append(item)
					yield

				self.disk_usage = sum(f.size for f in files if f.is_file)

				self.scroll_offset = 0
				self.filenames = filenames
				self.infostring = ' %d' % len(self.filenames) # update the infostring
				self.files = files

				self._clear_marked_items()
				for item in self.files:
					if item.path in marked_paths:
						self.mark_item(item, True)
					else:
						self.mark_item(item, False)

				self.old_sort_directories_first = None
				self.sort()

				if len(self.files) > 0:
					if self.pointed_obj is not None:
						self.sync_index()
					else:
						self.move(absolute=0)
			else:
				self.filenames = None
				self.files = None
				self.infostring = BAD_INFO

			self.cycle_list = None
			self.content_loaded = True
			self.last_update_time = time()

		finally:
			self.loading = False

	def unload(self):
		self.loading = False
		self.load_generator = None

	def load_content(self, schedule=None):
		"""
		Loads the contents of the directory. Use this sparingly since
		it takes rather long.
		"""

		if not self.loading:
			self.load_once()

			if schedule is None:
				schedule = self.size > 30

			if self.load_generator is None:
				self.load_generator = self.load_bit_by_bit()

				if schedule and self.fm:
					self.fm.loader.add(self)
				else:
					for _ in self.load_generator:
						pass
					self.load_generator = None

			elif not schedule or not self.fm:
				for _ in self.load_generator:
					pass
				self.load_generator = None


	def sort(self):
		"""Sort the containing files"""
		if self.files is None:
			return

		old_pointed_obj = self.pointed_obj
		try:
			sort_func = self.sort_dict[self.settings.sort]
		except:
			sort_func = sort_by_basename

		if self.settings.sort_case_insensitive and \
				sort_func == sort_by_basename:
			sort_func = sort_by_basename_icase

		self.files.sort(key = sort_func)

		if self.settings.sort_reverse:
			self.files.reverse()

		if self.settings.sort_directories_first:
			self.files.sort(key = sort_by_directory)

		if self.pointer is not None:
			self.move_to_obj(old_pointed_obj)
		else:
			self.correct_pointer()

		self.old_sort_directories_first = self.settings.sort_directories_first
		self.old_sort = self.settings.sort
		self.old_sort_reverse = self.settings.sort_reverse
		self.old_sort_case_insensitive = self.settings.sort_case_insensitive

	def sort_if_outdated(self):
		"""Sort the containing files if they are outdated"""
		if self.old_sort_directories_first != \
				self.settings.sort_directories_first \
				or self.old_sort != self.settings.sort \
				or self.old_sort_reverse != self.settings.sort_reverse \
				or self.old_sort_case_insensitive != \
				self.settings.sort_case_insensitive:
			self.sort()
			return True
		return False

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

		length = len(self)

		if forward:
			generator = ((self.pointer + (x + 1)) % length \
					for x in range(length-1))
		else:
			generator = ((self.pointer - (x + 1)) % length \
					for x in range(length-1))

		for i in generator:
			_file = self.files[i]
			if fnc(_file):
				self.pointer = i
				self.pointed_obj = _file
				self.correct_pointer()
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

	def correct_pointer(self):
		"""Make sure the pointer is in the valid range"""
		Accumulator.correct_pointer(self)

		try:
			if self == self.fm.env.cwd:
				self.fm.env.cf = self.pointed_obj
		except:
			pass

	def load_content_once(self, *a, **k):
		"""Load the contents of the directory if not done yet"""
		if not self.content_loaded:
			self.load_content(*a, **k)
			return True
		return False

	def load_content_if_outdated(self, *a, **k):
		"""
		Load the contents of the directory if it's
		outdated or not done yet
		"""

		if self.load_content_once(*a, **k): return True

		if self.old_show_hidden != self.settings.show_hidden or \
				self.old_filter != self.filter or \
				self.old_hidden_filter != self.settings.hidden_filter:
			self.old_filter = self.filter
			self.old_hidden_filter = self.settings.hidden_filter
			self.old_show_hidden = self.settings.show_hidden
			self.load_content(*a, **k)
			return True

		try:
			real_mtime = os.stat(self.path).st_mtime
		except OSError:
			real_mtime = None
		if self.stat:
			cached_mtime = self.load_content_mtime
		else:
			cached_mtime = 0

		if real_mtime != cached_mtime:
			self.load_content(*a, **k)
			return True
		return False

	def empty(self):
		"""Is the directory empty?"""
		return self.files is None or len(self.files) == 0

	def __nonzero__(self):
		"""Always True"""
		return True
	__bool__ = __nonzero__

	def __len__(self):
		"""The number of containing files"""
		if not self.accessible or not self.content_loaded:
			raise ranger.fsobject.NotLoadedYet()
		return len(self.files)

	def __eq__(self, other):
		"""Check for equality of the directories paths"""
		return isinstance(other, Directory) and self.path == other.path

	def __neq__(self, other):
		"""Check for inequality of the directories paths"""
		return not self.__eq__(other)

	def __hash__(self):
		return hash(self.path)
