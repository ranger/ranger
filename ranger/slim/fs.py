import os.path
from os.path import join, abspath, expanduser
from ranger.ext.lazy_property import lazy_property
from ranger.ext.calculate_scroll_pos import calculate_scroll_pos

def npath(path):
	if path[0] == '~':
		return abspath(expanduser(path))
	return abspath(path)

class File(object):
	def __init__(self, path, parent):
		self.path = path
		self.parent = parent

	@lazy_property
	def basename(self):
		return os.path.basename(self.path)

	@lazy_property
	def is_dir(self):
		return self.stat.st_mode & 0o170000 == 0o040000

	@lazy_property
	def stat(self):
		return os.lstat(self.path)

class Directory(File):
	pointer = 0
	scroll_begin = 0

	def load(self):
		try: filenames = os.listdir(self.path)
		except: return
		filenames.sort()
		files = [File(npath(self.path + '/' + path), self) \
				for path in filenames if not path[0] == '.']
		files.sort(key=lambda f: not f.is_dir)
		self.files = files

	def sync_pointer(self, winsize):
		self.scroll_begin = calculate_scroll_pos(winsize, len(self.files),
				self.pointer, self.scroll_begin)

	@lazy_property
	def files(self):
		self.load()
		return self.files

	@property
	def current_file(self):
		try:
			return self.files[self.pointer]
		except:
			return None
