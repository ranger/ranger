import fsobject
import file, debug

class Directory(fsobject.FSObject):
	def __init__(self, path):
		fsobject.FSObject.__init__(self, path)
		self.content_loaded = False
		self.scheduled = False
		self.enterable = False

		self.filenames = None
		self.files = None
		self.filter = None
		self.pointed_index = None
	
	def load_content(self):
		self.stop_if_frozen()
		self.load_if_outdated()
		self.content_loaded = True
		import os
		if self.exists:
			basenames = os.listdir(self.path)
			mapped = map(lambda name: os.path.join(self.path, name), basenames)
			self.filenames = list(mapped)
			self.infostring = ' %d' % len(self.filenames)
			debug.log('infostring set!')
			self.files = []
			for name in self.filenames:
				if os.path.isdir(name):
					f = Directory(name)
				else:
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
		return self.files[key]

if __name__ == '__main__':
	d = Directory('.')
	d.load_filenames()
	print(d.filenames)
	print(d[1])

