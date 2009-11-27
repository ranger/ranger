import os
from ranger.directory import Directory

class Vector():
	def __init__(self, x, y):
		self.x = x
		self.y = y

class Environment():
	# A collection of data which is relevant for more than
	# one class.
	def __init__(self, opt):
		self.opt = opt
		self.path = None
		self.pathway = ()
		self.directories = {}
		self.pwd = None # current directory
		self.cf = None # current file
		self.keybuffer = ()
		self.copy = None
		self.termsize = Vector(80, 24)

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
			return self.cf

	def get_directory(self, path):
		import os
		path = os.path.abspath(path)
		try:
			return self.directories[path]
		except KeyError:
			self.directories[path] = Directory(path)
			return self.directories[path]

	def enter_dir(self, path):
		# get the absolute path
		path = os.path.normpath(os.path.join(self.path, path))

		self.path = path
		self.pwd = self.get_directory(path)

		self.pwd.load_content()

		# build the pathway, a tuple of directory objects which lie
		# on the path to the current directory.
		if path == '/':
			self.pathway = (self.get_directory('/'), )
		else:
			pathway = []
			currentpath = '/'
			for dir in path.split('/'):
				currentpath = os.path.join(currentpath, dir)
#			debug.log(currentpath)
				pathway.append(self.get_directory(currentpath))
			self.pathway = tuple(pathway)

		# set the current file.
		if len(self.pwd) > 0:
			self.cf = self.pwd[0]
		else:
			self.cf = None
