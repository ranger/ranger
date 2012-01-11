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

import os.path
from os import stat as os_stat, lstat as os_lstat
from collections import deque
from time import time

from ranger.fsobject import BAD_INFO
from ranger.core.loader import Loadable
from ranger.ext.mount_path import mount_path
from ranger.fsobject import File, FileSystemObject
from ranger.core.shared import SettingsAware
from ranger.ext.accumulator import Accumulator
from ranger.ext.lazy_property import lazy_property
from ranger.ext.human_readable import human_readable

def sort_by_basename(path):
	"""returns path.basename (for sorting)"""
	return path.basename

def sort_by_basename_icase(path):
	"""returns case-insensitive path.basename (for sorting)"""
	return path.basename_lower

def sort_by_directory(path):
	"""returns 0 if path is a directory, otherwise 1 (for sorting)"""
	return 1 - path.is_directory

def sort_naturally(path):
	return path.basename_natural

def sort_naturally_icase(path):
	return path.basename_natural_lower

def accept_file(fname, dirname, hidden_filter, name_filter):
	if hidden_filter:
		try:
			if hidden_filter.search(fname):
				return False
		except:
			if hidden_filter in fname:
				return False
	if name_filter and name_filter not in fname:
		return False
	return True

class Directory(FileSystemObject, Accumulator, Loadable, SettingsAware):
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

	mount_path = '/'
	disk_usage = 0

	last_update_time = -1
	load_content_mtime = -1

	order_outdated = False
	content_outdated = False
	content_loaded = False

	_cumulative_size_calculated = False

	sort_dict = {
		'basename': sort_by_basename,
		'natural': sort_naturally,
		'size': lambda path: -path.size,
		'mtime': lambda path: -(path.stat and path.stat.st_mtime or 1),
		'ctime': lambda path: -(path.stat and path.stat.st_ctime or 1),
		'atime': lambda path: -(path.stat and path.stat.st_atime or 1),
		'type': lambda path: path.mimetype or '',
	}

	def __init__(self, path, **kw):
		assert not os.path.isfile(path), "No directory given!"

		Accumulator.__init__(self)
		FileSystemObject.__init__(self, path, **kw)

		self.marked_items = list()

		for opt in ('sort_directories_first', 'sort', 'sort_reverse',
				'sort_case_insensitive'):
			self.settings.signal_bind('setopt.' + opt,
					self.request_resort, weak=True, autosort=False)

		for opt in ('hidden_filter', 'show_hidden'):
			self.settings.signal_bind('setopt.' + opt,
				self.request_reload, weak=True, autosort=False)
		self.use()

	def request_resort(self):
		self.order_outdated = True

	def request_reload(self):
		self.content_outdated = True

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

	# XXX: Is it really necessary to have the marked items in a list?
	# Can't we just recalculate them with [f for f in self.files if f.marked]?
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

	# XXX: Check for possible race conditions
	def load_bit_by_bit(self):
		"""
		Returns a generator which load a part of the directory
		in each iteration.
		"""

		self.loading = True
		self.load_if_outdated()

		try:
			if self.runnable:
				yield
				mypath = self.path

				self.mount_path = mount_path(mypath)

				hidden_filter = not self.settings.show_hidden \
						and self.settings.hidden_filter
				filelist = os.listdir(mypath)

				if self._cumulative_size_calculated:
					# If self.content_loaded is true, this is not the first
					# time loading.  So I can't really be sure if the
					# size has changed and I'll add a "?".
					if self.content_loaded:
						if self.fm.settings.autoupdate_cumulative_size:
							self.look_up_cumulative_size()
						else:
							self.infostring = ' %s' % human_readable(
								self.size, separator='? ')
					else:
						self.infostring = ' %s' % human_readable(self.size)
				else:
					self.size = len(filelist)
					self.infostring = ' %d' % self.size
				if self.is_link:
					self.infostring = '->' + self.infostring

				filenames = [mypath + (mypath == '/' and fname or '/' + fname)\
						for fname in filelist if accept_file(
							fname, mypath, hidden_filter, self.filter)]
				yield

				self.load_content_mtime = os.stat(mypath).st_mtime

				marked_paths = [obj.path for obj in self.marked_items]

				files = []
				disk_usage = 0
				for name in filenames:
					try:
						file_lstat = os_lstat(name)
						if file_lstat.st_mode & 0o170000 == 0o120000:
							file_stat = os_stat(name)
						else:
							file_stat = file_lstat
						stats = (file_stat, file_lstat)
						is_a_dir = file_stat.st_mode & 0o170000 == 0o040000
					except:
						stats = None
						is_a_dir = False
					if is_a_dir:
						try:
							item = self.fm.env.get_directory(name)
							item.load_if_outdated()
						except:
							item = Directory(name, preload=stats,
									path_is_abs=True)
							item.load()
					else:
						item = File(name, preload=stats, path_is_abs=True)
						item.load()
						disk_usage += item.size
					files.append(item)
					yield
				self.disk_usage = disk_usage

				self.filenames = filenames
				self.files = files

				self._clear_marked_items()
				for item in self.files:
					if item.path in marked_paths:
						item._mark(True)
						self.marked_items.append(item)
					else:
						item._mark(False)

				self.sort()

				if files:
					if self.pointed_obj is not None:
						self.sync_index()
					else:
						self.move(to=0)
			else:
				self.filenames = None
				self.files = None

			self.cycle_list = None
			self.content_loaded = True
			self.last_update_time = time()
			self.correct_pointer()

		finally:
			self.loading = False
			self.fm.signal_emit("finished_loading_dir", directory=self)

	def unload(self):
		self.loading = False
		self.load_generator = None

	def load_content(self, schedule=None):
		"""
		Loads the contents of the directory. Use this sparingly since
		it takes rather long.
		"""
		self.content_outdated = False

		if not self.loading:
			if not self.loaded:
				self.load()

			if not self.accessible:
				self.content_loaded = True
				return

			if schedule is None:
				schedule = True   # was: self.size > 30

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

		if self.settings.sort_case_insensitive and \
				sort_func == sort_naturally:
			sort_func = sort_naturally_icase

		self.files.sort(key = sort_func)

		if self.settings.sort_reverse:
			self.files.reverse()

		if self.settings.sort_directories_first:
			self.files.sort(key = sort_by_directory)

		if self.pointer is not None:
			self.move_to_obj(old_pointed_obj)
		else:
			self.correct_pointer()

	def _get_cumulative_size(self):
		if self.size == 0:
			return 0
		cum = 0
		realpath = os.path.realpath
		for dirpath, dirnames, filenames in os.walk(self.path,
				onerror=lambda _: None):
			for file in filenames:
				try:
					if dirpath == self.path:
						stat = os_stat(realpath(dirpath + "/" + file))
					else:
						stat = os_stat(dirpath + "/" + file)
					cum += stat.st_size
				except:
					pass
		return cum

	def look_up_cumulative_size(self):
		self._cumulative_size_calculated = True
		self.size = self._get_cumulative_size()
		self.infostring = ('-> ' if self.is_link else ' ') + \
				human_readable(self.size)

	@lazy_property
	def size(self):
		try:
			size = len(os.listdir(self.path))  # bite me
		except OSError:
			self.infostring = BAD_INFO
			self.accessible = False
			self.runnable = False
			return 0
		else:
			self.infostring = ' %d' % size
			self.accessible = True
			self.runnable = True
			return size

	@lazy_property
	def infostring(self):
		self.size  # trigger the lazy property initializer
		if self.is_link:
			return '->' + self.infostring
		return self.infostring

	@lazy_property
	def runnable(self):
		self.size  # trigger the lazy property initializer
		return self.runnable

	def sort_if_outdated(self):
		"""Sort the containing files if they are outdated"""
		if self.order_outdated:
			self.order_outdated = False
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

	def search_fnc(self, fnc, offset=1, forward=True):
		if not hasattr(fnc, '__call__'):
			return False

		length = len(self)

		if forward:
			generator = ((self.pointer + (x + offset)) % length \
					for x in range(length - 1))
		else:
			generator = ((self.pointer - (x + offset)) % length \
					for x in range(length - 1))

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

		if self.files is None or self.content_outdated:
			self.load_content(*a, **k)
			return True

		try:
			real_mtime = os.stat(self.path).st_mtime
		except OSError:
			real_mtime = None
			return False
		if self.stat:
			cached_mtime = self.load_content_mtime
		else:
			cached_mtime = 0

		if real_mtime != cached_mtime:
			self.load_content(*a, **k)
			return True
		return False

	def get_description(self):
		return "Loading " + str(self)

	def use(self):
		"""mark the filesystem-object as used at the current time"""
		self.last_used = time()

	def is_older_than(self, seconds):
		"""returns whether this object wasn't use()d in the last n seconds"""
		if seconds < 0:
			return True
		return self.last_used + seconds < time()

	def go(self, history=True):
		"""enter the directory if the filemanager is running"""
		if self.fm:
			return self.fm.enter_dir(self.path, history=history)
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
		assert self.accessible
		assert self.content_loaded
		assert self.files is not None
		return len(self.files)

	def __eq__(self, other):
		"""Check for equality of the directories paths"""
		return isinstance(other, Directory) and self.path == other.path

	def __neq__(self, other):
		"""Check for inequality of the directories paths"""
		return not self.__eq__(other)

	def __hash__(self):
		return hash(self.path)
