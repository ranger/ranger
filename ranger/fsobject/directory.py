from . import BAD_INFO
from .file import File
from .fsobject import FileSystemObject as SuperClass
from ranger.shared import SettingsAware
import ranger.fsobject

def sort_by_basename(path):
	"""returns path.basename (for sorting)"""
	return path.basename

def sort_by_directory(path):
	"""returns 0 if path is a directory, otherwise 1 (for sorting)"""
	return 1 - int( isinstance( path, Directory ) )

class NoDirectoryGiven(Exception):
	pass

class Directory(SuperClass, SettingsAware):
	content_loaded = False
	scheduled = False
	enterable = False

	filenames = None
	files = None
	filter = None
	pointed_index = None
	pointed_file = None
	scroll_begin = 0
	scroll_offset = 0

	old_show_hidden = None
	old_directories_first = None

	def __init__(self, path):
		from os.path import isfile

		if isfile(path):
			raise NoDirectoryGiven()

		SuperClass.__init__(self, path)

		# to find out if something has changed:
		self.old_show_hidden = self.settings.show_hidden
		self.old_directories_first = self.settings.directories_first

	def load_content(self):
		from os.path import join, isdir, basename
		from os import listdir

		self.load_if_outdated()
		self.content_loaded = True

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
			files = []
			for name in self.filenames:
				if isdir(name):
					f = Directory(name)
				else:
					f = File(name)
				f.load()
				files.append(f)

			self.files = files
			self.old_directories_first = None
#			self.sort()

			if len(self.files) > 0:
				if self.pointed_file is not None:
					self.move_pointer_to_file_path(self.pointed_file)
#				if self.pointed_file is None:
#					self.correct_pointer()
		else:
			self.filenames = None
			self.files = None
			self.infostring = BAD_INFO

	def sort(self):
		if self.files is None:
			return

		old_pointed_file = self.pointed_file
		self.files.sort(key = sort_by_basename)

		if self.settings.directories_first:
			self.files.sort(key = sort_by_directory)

		if self.pointed_index is not None:
			self.move_pointer_to_file_path(old_pointed_file)
		else:
			self.correct_pointer()

		self.old_directories_first = self.settings.directories_first
	
	def sort_if_outdated(self):
		if self.old_directories_first != self.settings.directories_first:
			self.sort()

	# Notice: fm.env.cf should always point to the current file. If you
	# modify the current directory with this function, make sure
	# to update fm.env.cf aswell.
	def move_pointer(self, relative=0, absolute=None):
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
		if path is None: return
		try: path = path.path
		except AttributeError: pass

		self.load_content_once()
		if self.empty(): return

		i = 0
		for f in self.files:
			if f.path == path:
				self.move_pointer(absolute = i)
				return True
			i += 1
		return False
	
	def search(self, arg, direction = 1):
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
		"""make sure the pointer is in the valid range of 0 : len(self.files)-1 (or None if directory is empty.)"""

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
		
	def load_content_once(self):
		if not self.content_loaded:
			self.load_content()
			return True
		return False

	def load_content_if_outdated(self):
		if self.load_content_once(): return True

		if self.old_show_hidden != self.settings.show_hidden:
			self.old_show_hidden = self.settings.show_hidden
			self.load_content()
			return True

		import os
		real_mtime = os.stat(self.path).st_mtime
		cached_mtime = self.stat.st_mtime

		if real_mtime != cached_mtime:
			self.load_content()
			return True
		return False

	def empty(self):
		return self.files is None or len(self.files) == 0

	def __nonzero__(self):
		return True

	def __len__(self):
		if not self.accessible: raise ranger.fsobject.NotLoadedYet()
		return len(self.files)
	
	def __getitem__(self, key):
		if not self.accessible: raise ranger.fsobject.NotLoadedYet()
		return self.files[key]

	def __eq__(self, other):
		return isinstance(other, Directory) and self.path == other.path

	def __neq__(self, other):
		return not self.__eq__(other)
