class FrozenException(Exception): pass

class Directory():
	def __init__(self, path):
		self.path = path
		self.files_loaded = False
		self.scheduled = False
		self.files = None
		self.mtime = None
		self.exists = True

		self.frozen = False

	def load_files(self):
		import os
		if self.frozen: raise FrozenException()
		try:
			self.files = os.listdir(self.path)
			self.exists = True
		except OSError:
			self.files = []
			self.exists = False
		self.files_loaded = True

	def clone(self):
		clone = Directory(self.path)
		for key in iter(self.__dict__):
			clone.__dict__[key] = self.__dict__[key]
		return clone

	def frozenClone(self):
		clone = self.clone()
		clone.frozen = True
		return clone

	def __len__(self):
		return len(self.files)
	
	def __getitem__(self, key):
		return self.files[key]

if __name__ == '__main__':
	d = Directory('.')
	d.load_files()
	print(d.files)
	print(d[1])

	
