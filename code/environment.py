class Vector():
	def __init__(self, x, y):
		self.x = x
		self.y = y

class Environment():
	# A collection of data which is relevant for more than
	# one class.
	def __init__(self):
		self.path = None
		self.directories = {}
		self.pwd = None # current directory
		self.cf = None # current file
		self.keybuffer = ''
		self.copy = None
		self.termsize = Vector(80, 24)
