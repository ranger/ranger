from string import ascii_letters, digits
ALLOWED_KEYS = ascii_letters + digits + "`'"

class NonexistantBookmark(Exception):
	pass

class Bookmarks(object):
	def __init__(self, path = None):
		import string, re, os
		self.dct = {}
		if path is None:
			self.path = os.path.expanduser("~/.ranger/bookmarks")
		self.load_pattern = re.compile(r"^[\d\w`']:.")
		self.enter_dir_function = None

	def load(self):
		import os
		self.dct.clear()

		if os.access(self.path, os.R_OK):
			f = open(self.path, 'r')
			for line in f:
				if self.load_pattern.match(line):
					key, value = line[0], line[2:-1]
					if key in ALLOWED_KEYS: 
						self.dct[key] = value

			f.close()

	def enter(self, key):
		if self.enter_dir_function is not None:
			self.enter_dir_function(self[key])
		else:
			raise RuntimeError('Not specified how to enter a directory')

	def remember(self, value):
		self["`"] = value
		self["'"] = value

	def __getitem__(self, key):
		if key in self.dct:
			return self.dct[key]
		else:
			raise NonexistantBookmark()

	def __setitem__(self, key, value):
		if key in ALLOWED_KEYS:
			self.dct[key] = value
			self.save()

	def __contains__(self, key):
		return key in self.dct

	def save(self):
		import os
		if os.access(self.path, os.W_OK):
			f = open(self.path, 'w')

			for key, value in self.dct.items():
				if type(key) == str\
						and type(value) == str \
						and key in ALLOWED_KEYS:
					f.write("{0}:{1}\n".format(str(key), str(value)))

			f.close()
