import os.path
from ranger.ext.lazy_property import lazy_property

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
		return os.stat(self.path)

class Directory(File):
	files = None
	pointer = 0
	scroll_begin = 0
	def load(self):
		if self.files is None:
			try:
				files = os.listdir(self.path)
			except:
				return
			files.sort()
			self.files = [File(path, self) for path in files if not path[0] == '.']

	@property
	def current_file(self):
		return self.files[self.pointer]
