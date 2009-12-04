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
		self.last_mtime = None

	def load_dict(self):
		import os
		dct = {}
		if os.access(self.path, os.R_OK):
			f = open(self.path, 'r')
			for line in f:
				if self.load_pattern.match(line):
					key, value = line[0], line[2:-1]
					if key in ALLOWED_KEYS: 
						dct[key] = value
			f.close()
			return dct
		else:
			raise OSError('Cannot read the given path')
	
	def set_dict(self, dct):
		self.dct.clear()
		self.dct.update(dct)
		self.original_dict = self.dct.copy()
		self.last_mtime = self.get_mtime()

	def get_mtime(self):
		import os
		return os.stat(self.path).st_mtime

	def load(self):
		try:
			new_dict = self.load_dict()
		except OSError:
			return

		self.set_dict(new_dict)
	
	def delete(self, key):
		if key in self.dct:
			del self.dct[key]
			self.save()

	def update(self):
		try:
			real_dict = self.load_dict()
		except OSError:
			return

		for key in set(self.dct.keys()) | set(real_dict.keys()):
			if key in self.dct:
				current = self.dct[key]
			else:
				current = None
			
			if key in self.original_dict:
				original = self.original_dict[key]
			else:
				original = None
				
			if key in real_dict:
				real = real_dict[key]
			else:
				real = None

			if current == original and current != real:
				continue

			if key not in self.dct:
				del real_dict[key]
			else:
				real_dict[key] = current

		self.set_dict(real_dict)

	def reload_if_outdated(self):
		if self.last_mtime != self.get_mtime():
			self.update()

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
		self.update()
		if os.access(self.path, os.W_OK):
			f = open(self.path, 'w')

			for key, value in self.dct.items():
				if type(key) == str\
						and type(value) == str \
						and key in ALLOWED_KEYS:
					f.write("{0}:{1}\n".format(str(key), str(value)))

			f.close()
