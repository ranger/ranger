import directory

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
		self.keybuffer = ''
		self.copy = None
		self.termsize = Vector(80, 24)
	
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
			self.directories[path] = directory.Directory(path)
			return self.directories[path]
