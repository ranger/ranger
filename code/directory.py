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
		self.pointed_file = None
		self.index = None
	
	def load_content(self):
		self.stop_if_frozen()
		self.load_if_outdated()
		self.content_loaded = True
		import os
		if self.exists:
			basenames = os.listdir(self.path)
			mapped = map(lambda name: os.path.join(self.path, name), basenames)
			self.filenames = list(mapped)
			self.infostring = ' %d' % len(self.filenames) # update the infostring
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
		if not self.content_loaded:
			self.load_content()
			return True
		return False

	def load_content_if_outdated(self):
		self.stop_if_frozen()
		if self.load_content_once(): return True

		import os
		real_mtime = os.stat(self.path).st_mtime
		cached_mtime = self.stat.st_mtime

		if real_mtime != cached_mtime:
			self.load_content()
			return True
		return False

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

