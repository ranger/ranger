from ranger.fsobject import BAD_INFO, File, FileSystemObject
from ranger.shared import SettingsAware
from ranger import log
import ranger.fsobject

def sort_by_basename(path):
	"""returns path.basename (for sorting)"""
	return path.basename

def sort_by_directory(path):
	"""returns 0 if path is a directory, otherwise 1 (for sorting)"""
	return 1 - int( isinstance( path, Directory ) )

class NoDirectoryGiven(Exception):
	pass

class Directory(FileSystemObject, SettingsAware):
	enterable = False
	load_generator = None
	loading = False

	filenames = None
	files = None
	filter = None
	marked_items = None
	pointed_index = None
	pointed_file = None
	scroll_begin = 0
	scroll_offset = 0

	old_show_hidden = None
	old_directories_first = None
	old_reverse = None
	old_sort = None

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

		FileSystemObject.__init__(self, path)

		self.marked_items = set()

		# to find out if something has changed:
		self.old_show_hidden = self.settings.show_hidden
		self.old_directories_first = self.settings.directories_first
		self.old_sort = self.settings.sort
		self.old_reverse = self.settings.reverse
	
	def mark_item(self, item, val):
		item._mark(val)
		if val:
			if item in self.files:
				self.marked_items.add(item)
		else:
			if item in self.marked_items:
				self.marked_items.remove(item)

	def toggle_mark(self, item):
		self.mark_item(item, not item.marked)

	def toggle_all_marks(self):
		for item in self.files:
			self.toggle_mark(item)
	
	def mark_all(self, val):
		for item in self.files:
			self.mark_item(item, val)

		if not val:
			self.marked_items.clear()
			self._clear_marked_items()
	
	def _gc_marked_items(self):
		for item in self.marked_items.copy():
			if item.path not in self.filenames:
				self.marked_items.remove(item)
	
	def _clear_marked_items(self):
		for item in self.marked_items:
			item._mark(False)
		self.marked_items.clear()

	def get_selection(self):
		"""READ ONLY"""
		self._gc_marked_items()
		if self.marked_items:
			return set(self.marked_items)
		elif self.pointed_file:
			return set([self.pointed_file])
		else:
			return set()
	
	def load_bit_by_bit(self):
		"""
		Returns a generator which load a part of the directory
		in each iteration.
		"""

#		log("generating loader for " + self.path + "(" + str(id(self)) + ")")
		from os.path import join, isdir, basename
		from os import listdir

		self.loading = True
		self.load_if_outdated()
		yield

		if self.exists and self.runnable:
			filenames = []
			for fname in listdir(self.path):
				if not self.settings.show_hidden and fname[0] == '.':
					continue
				if isinstance(self.filter, str) and self.filter in fname:
					continue
				filenames.append(join(self.path, fname))
			self.scroll_offset = 0
			self.filenames = filenames
			self.infostring = ' %d' % len(self.filenames) # update the infostring
			yield

			marked_paths = set(map( \
					lambda obj: obj.path, self.marked_items))
			self._clear_marked_items()

			files = []
			for name in self.filenames:
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

			self.files = files

			for item in self.files:
				if item.path in marked_paths:
					self.mark_item(item, True)
				else:
					self.mark_item(item, False)

			self.old_directories_first = None
			self.sort()

			if len(self.files) > 0:
				if self.pointed_file is not None:
					self.move_pointer_to_file_path(self.pointed_file)
		else:
			self.filenames = None
			self.files = None
			self.infostring = BAD_INFO

		self.content_loaded = True
		self.loading = False

	def unload(self):
		self.loading = False
		self.load_generator = None

	def load_content(self, schedule=False):
		"""
		Loads the contents of the directory. Use this sparingly since
		it takes rather long.
		"""

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

		old_pointed_file = self.pointed_file
		try:
			sort_func = self.sort_dict[self.settings.sort]
		except:
			sort_func = sort_by_basename
		self.files.sort(key = sort_func)

		if self.settings.reverse:
			self.files.reverse()

		if self.settings.directories_first:
			self.files.sort(key = sort_by_directory)

		if self.pointed_index is not None:
			self.move_pointer_to_file_path(old_pointed_file)
		else:
			self.correct_pointer()

		self.old_directories_first = self.settings.directories_first
		self.old_sort = self.settings.sort
		self.old_reverse = self.settings.reverse
	
	def sort_if_outdated(self):
		"""Sort the containing files if they are outdated"""
		if self.old_directories_first != self.settings.directories_first \
				or self.old_sort != self.settings.sort \
				or self.old_reverse != self.settings.reverse:
			self.sort()

	# Notice: fm.env.cf should always point to the current file. If you
	# modify the current directory with this function, make sure
	# to update fm.env.cf aswell.
	def move_pointer(self, relative=0, absolute=None):
		"""Move the index pointer"""
		if self.empty(): return
		i = self.pointed_index
		if isinstance(absolute, int):
			if absolute < 0:
				absolute = len(self.files) + absolute
			i = absolute

		if isinstance(relative, int):
			i += relative

		self.pointed_index = i
		self.correct_pointer()
		return self.pointed_file

	def move_pointer_to_file_path(self, path):
		"""
		Move the index pointer to the index of the file object
		with the given path.
		"""
		if path is None: return
		try: path = path.path
		except AttributeError: pass

		self.load_content_once()
		if self.empty(): return

		i = 0
		for f in self.files:
			if f.path == path:
				self.move_pointer(absolute = i)
				self.correct_pointer()
				return True
			i += 1

		return self.move_pointer(absolute=self.pointed_index)
	
	def search(self, arg, direction = 1):
		"""Search for a regular expression"""
		if self.empty() or arg is None:
			return False
		elif hasattr(arg, 'search'):
			fnc = lambda x: arg.search(x.basename)
		else:
			fnc = lambda x: arg in x.basename

		length = len(self)

		if direction > 0:
			generator = ((self.pointed_index + (x + 1)) % length for x in range(length-1))
		else:
			generator = ((self.pointed_index - (x + 1)) % length for x in range(length-1))

		for i in generator:
			_file = self.files[i]
			if fnc(_file):
				self.pointed_index = i
				self.pointed_file = _file
				return True
		return False

	def correct_pointer(self):
		"""Make sure the pointer is in the valid range"""

		if self.files is None or len(self.files) == 0:
			self.pointed_index = None
			self.pointed_file = None

		else:
			i = self.pointed_index

			if i is None: i = 0
			if i >= len(self.files): i = len(self.files) - 1
			if i < 0: i = 0

			self.pointed_index = i
			self.pointed_file = self[i]

		try:
			if self == self.fm.env.pwd:
				self.fm.env.cf = self.pointed_file
		except:
			pass
		
	def load_content_once(self, *a, **k):
		"""Load the contents of the directory if not done yet"""
		if not self.content_loaded:
			if not self.loading:
				self.load_content(*a, **k)
			return True
		return False

	def load_content_if_outdated(self, *a, **k):
		"""
		Load the contents of the directory if it's
		outdated or not done yet
		"""

		if self.load_content_once(*a, **k): return True

		if self.old_show_hidden != self.settings.show_hidden:
			self.old_show_hidden = self.settings.show_hidden
			self.load_content(*a, **k)
			return True

		import os
		try:
			real_mtime = os.lstat(self.path).st_mtime
		except OSError:
			real_mtime = None
		if self.stat:
			cached_mtime = self.stat.st_mtime
		else:
			cached_mtime = 0

		if real_mtime != cached_mtime:
			self.load_content()
			return True
		return False

	def empty(self):
		"""Is the directory empty?"""
		return self.files is None or len(self.files) == 0

	def __nonzero__(self):
		"""Always True"""
		return True

	def __len__(self):
		"""The number of containing files"""
		if not self.accessible: raise ranger.fsobject.NotLoadedYet()
		return len(self.files)
	
	def __getitem__(self, key):
		"""Get the file by its index"""
		if not self.accessible: raise ranger.fsobject.NotLoadedYet()
		return self.files[key]

	def __eq__(self, other):
		"""Check for equality of the directories paths"""
		return isinstance(other, Directory) and self.path == other.path

	def __neq__(self, other):
		"""Check for inequality of the directories paths"""
		return not self.__eq__(other)
	
	def __hash__(self):
		return hash(self.path)
