class FrozenException(Exception): pass
class NotLoadedYet(Exception): pass

class Directory():
	def __init__(self, path):
		self.path = path
		self.accessible = False
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
			self.mtime = os.path.getmtime(self.path)
			self.files = os.listdir(self.path)
			self.exists = True
			self.accessible = True
		except OSError:
			self.files = None
			self.exists = False
			self.accessible = False

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
		if not self.accessible: raise NotLoadedYet()
		return len(self.files)
	
	def __getitem__(self, key):
		if not self.accessible: raise NotLoadedYet()
		return self.files[key]

if __name__ == '__main__':
	d = Directory('.')
	d.load_files()
	print(d.files)
	print(d[1])

