import fsobject
import file

class Directory(fsobject.FSObject):
	def __init__(self, path):
		fsobject.FSObject.__init__(self, path)
		self.content_loaded = False
		self.scheduled = False
		self.enterable = False

		self.filenames = None
		self.files = None
		self.pointed_index = None
	
	def load_content(self):
		self.stop_if_frozen()
		self.load_if_outdated()
		self.content_loaded = True
		import os
		if self.exists:
			self.filenames = os.listdir(self.path)
			self.files = []
			for name in self.filenames:
				f = file.File(name)
				f.load()
				self.files.append(f)
	
	def load_content_once(self):
		self.stop_if_frozen()
		if not self.content_loaded: self.load_content()

	def __len__(self):
		if not self.accessible: raise fsobject.NotLoadedYet()
		return len(self.filenames)
	
	def __getitem__(self, key):
		if not self.accessible: raise fsobject.NotLoadedYet()
		return self.filenames[key]

if __name__ == '__main__':
	d = Directory('.')
	d.load_filenames()
	print(d.filenames)
	print(d[1])

