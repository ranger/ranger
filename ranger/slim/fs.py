import os.path
from os.path import join, abspath, expanduser, normpath
from ranger.ext.lazy_property import lazy_property
from ranger.ext.calculate_scroll_pos import calculate_scroll_pos

def npath(path, cwd='.'):
	if not path:
		return '/'
	if path[0] == '~':
		return normpath(join(cwd, expanduser(path)))
	return normpath(join(cwd, path))

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
		return self.stat.st_mode & 0o170000 == 0o040000

	@lazy_property
	def is_link(self):
		return self.stat.st_mode & 0o170000 == 0o120000

	@lazy_property
	def stat(self):
			result = os.lstat(self.path)
			if result.st_mode & 0o170000 == 0o120000:
				self.is_link = True
				try:
					return os.stat(self.path)
				except OSError:
					pass
			else:
				self.is_link = False
			return result


	@lazy_property
	def permission_string(self):
		if self.is_dir:
			perms = ['d']
		elif self.is_link:
			perms = ['l']
		else:
			perms = ['-']

		mode = self.stat.st_mode
		test = 0o0400
		while test:  # will run 3 times because 0o400 >> 9 = 0
			for what in "rwx":
				if mode & test:
					perms.append(what)
				else:
					perms.append('-')
				test >>= 1

		self.permissions = ''.join(perms)
		return self.permissions

class Directory(File):
	pointer = 0
	scroll_begin = 0
	_files = None

	def load(self):
		try: filenames = os.listdir(self.path)
		except: return
		filenames.sort(key=lambda s: s.lower())
		files = [File(npath(path, self.path), self) \
				for path in filenames if not path[0] == '.']
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
