from os.path import abspath, normpath, join, expanduser
from ranger.directory import Directory, NoDirectoryGiven

class Environment():
	# A collection of data which is relevant for more than
	# one class.
	def __init__(self, path, opt):
		self.path = abspath(expanduser(path))
		self.opt = opt
		self.pathway = ()
		self.directories = {}
		self.pwd = None # current directory
		self.cf = None # current file
		self.keybuffer = ()
		self.copy = None
		self.termsize = (24, 80)
		self.history = []
		self.history_position = -1

	def key_append(self, key):
		self.keybuffer += (key, )

	def key_clear(self):
		self.keybuffer = ()
	
	def at_level(self, level):
		if level <= 0:
			try:
				return self.pathway[level - 1]
			except IndexError:
				return None
		else:
			try:
				return self.directories[self.cf.path]
			except AttributeError:
				return None
			except KeyError:
				return self.cf
	
	def get_directory(self, path):
		path = abspath(path)
		try:
			return self.directories[path]
		except KeyError:
			self.directories[path] = Directory(path)
			return self.directories[path]

	def assign_correct_cursor_positions(self):
		# Assign correct cursor positions for subdirectories
		last_path = None
		for path in reversed(self.pathway):
			if last_path is None:
				last_path = path
				continue

			path.move_pointer_to_file_path(last_path)
			last_path = path
	
	def history_go(self, relative):
		if not self.history:
			return

		if self.history_position == -1:
			if relative > 0:
				return
			elif relative < 0:
				self.history_position = max( 0, len(self.history) - 1 + relative )
		else:
			self.history_position += relative
			if self.history_position < 0:
				self.history_position = 0

		if self.history_position >= len(self.history) - 1:
			self.history_position = -1

		self.enter_dir(self.history[self.history_position], history=False)

	def history_add(self, path):
		if self.opt['max_history_size']:
			if len(self.history) > self.history_position > (-1):
				self.history = self.history[0 : self.history_position + 1]
			if not self.history or (self.history and self.history[-1] != path):
				self.history_position = -1
				self.history.append(path)
			if len(self.history) > self.opt['max_history_size']:
				self.history.pop(0)

	def enter_dir(self, path, history = True):
		path = str(path)

		# get the absolute path
		path = normpath(join(self.path, expanduser(path)))

		try:
			new_pwd = self.get_directory(path)
		except NoDirectoryGiven:
			return False

		self.path = path
		self.pwd = new_pwd

		self.pwd.load_content_if_outdated()

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

		self.assign_correct_cursor_positions()

		# set the current file.
		self.pwd.directories_first = self.opt['directories_first']
		self.pwd.sort_if_outdated()
		self.cf = self.pwd.pointed_file

		if history:
			self.history_add(path)

		return True

