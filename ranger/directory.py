import ranger.fsobject
from ranger import file, debug

class NoDirectoryGiven(Exception):
	pass

class Directory(ranger.fsobject.FSObject):
	def __init__(self, path):
		from os.path import isdir
		if not isdir(path): raise NoDirectoryGiven()
		ranger.fsobject.FSObject.__init__(self, path)
		self.content_loaded = False
		self.scheduled = False
		self.enterable = False

		self.filenames = None
		self.files = None
		self.filter = None
		self.pointed_index = None
		self.pointed_file = None
		self.scroll_begin = 0
		self.show_hidden = False
		self.old_show_hidden = self.show_hidden
	
	def set_filter(self, string):
		self.filter = string
		self.load_content()
	
	def load_content(self):
		from os.path import join, isdir, basename
		from os import listdir

		self.stop_if_frozen()
		self.load_if_outdated()
		self.content_loaded = True

		if self.exists and self.runnable:
			filenames = []
			for fname in listdir(self.path):
				if not self.show_hidden and fname[0] == '.':
					continue
				if isinstance(self.filter, str) and self.filter in fname:
					continue
				filenames.append(join(self.path, fname))
#			basenames = listdir(self.path)
#			mapped = map(lambda name: join(self.path, name), basenames)
			self.scroll_offset = 0
			self.filenames = filenames
			self.infostring = ' %d' % len(self.filenames) # update the infostring
			files = []
			for name in self.filenames:
				if isdir(name):
					f = Directory(name)
				else:
					f = file.File(name)
				f.load()
				files.append(f)

			files.sort(key = lambda x: x.basename)
			self.files = files

			if len(self.files) > 0:
				self.pointed_index = 0
				self.pointed_file = self.files[0]
		else:
			self.filenames = None
			self.files = None
			self.infostring = ranger.fsobject.FSObject.BAD_INFO
	
	# Notice: fm.env.cf should always point to the current file. If you
	# modify the current directory with this function, make sure
	# to update fm.env.cf aswell.
	def move_pointer(self, relative=0, absolute=None):
		i = self.pointed_index
		if isinstance(absolute, int):
			if absolute < 0:
				absolute = len(self.files) + absolute
			i = absolute

		if isinstance(relative, int):
			i += relative

		self.pointed_index = i
		self.fix_pointer()
		return self.pointed_file

	def move_pointer_to_file_path(self, path):
		self.load_content_once()
		i = 0
		for f in self.files:
			if f.path == path:
				self.move_pointer(absolute = i)
				return
			i += 1


	def fix_pointer(self):
		i = self.pointed_index
		if i >= len(self.files): i = len(self.files) - 1
		if i < 0: i = 0
		self.pointed_index = i
		self.pointed_file = self[i]
		
	def load_content_once(self):
		self.stop_if_frozen()
		if not self.content_loaded:
			self.load_content()
			return True
		return False

	def load_content_if_outdated(self):
		self.stop_if_frozen()
		if self.load_content_once(): return True

		if self.old_show_hidden != self.show_hidden:
			self.old_show_hidden = self.show_hidden
			self.load_content()
			return True

		import os
		real_mtime = os.stat(self.path).st_mtime
		cached_mtime = self.stat.st_mtime

		if real_mtime != cached_mtime:
			self.load_content()
			return True
		return False

	def __len__(self):
		if not self.accessible: raise ranger.fsobject.NotLoadedYet()
		return len(self.filenames)
	
	def __getitem__(self, key):
		if not self.accessible: raise ranger.fsobject.NotLoadedYet()
		return self.files[key]

if __name__ == '__main__':
	d = Directory('.')
	d.load_filenames()
	print(d.filenames)
	print(d[1])

