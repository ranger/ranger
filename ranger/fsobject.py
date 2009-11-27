import ranger.fstype

class FrozenException(Exception): pass
class NotLoadedYet(Exception): pass

class FSObject(object):
	BAD_INFO = ''
	def __init__(self, path):
		if type(self) == FSObject:
			raise TypeError("FSObject is an abstract class and cannot be initialized.")
		from os.path import basename
		self.path = path
		self.basename = basename(path)
		self.exists = False
		self.accessible = False
		self.marked = False
		self.tagged = False
		self.frozen = False
		self.loaded = False
		self.runnable = False
		self.islink = False
		self.brokenlink = False
		self.stat = None
		self.infostring = None
		self.permissions = None
		self.type = ranger.fstype.Unknown
	
	def __str__(self):
		return str(self.path)

	# load() reads useful information about the file from the file system
	# and caches it in instance attributes.
	def load(self):
		self.stop_if_frozen()
		self.loaded = True

		import os
#		try:
		if os.access(self.path, os.F_OK):
			self.stat = os.stat(self.path)
			self.islink = os.path.islink(self.path)
			self.exists = True
			self.accessible = True

			if os.path.isdir(self.path):
				self.type = ranger.fstype.Directory
				try:
					self.infostring = ' %d' % len(os.listdir(self.path))
					self.runnable = True
				except OSError:
					self.infostring = FSObject.BAD_INFO
					self.runnable = False
					self.accessible = False
			elif os.path.isfile(self.path):
				self.type = ranger.fstype.File
				self.infostring = ' %d' % self.stat.st_size
			else:
				self.type = ranger.fstype.Unknown
				self.infostring = None

		else:
#		except OSError:
			self.islink = False
			self.infostring = None
			self.type = ranger.fstype.Nonexistent
			self.exists = False
			self.runnable = False
			self.accessible = False

	def load_once(self):
		self.stop_if_frozen()
		if not self.loaded:
			self.load()
			return True
		return False

	def load_if_outdated(self):
		self.stop_if_frozen()
		if self.load_once(): return True

		import os
		real_mtime = os.stat(self.path).st_mtime
		cached_mtime = self.stat.st_mtime

		if real_mtime != cached_mtime:
			self.load()
			return True
		return False

	def clone(self):
		clone = type(self)(self.path)
		for key in iter(self.__dict__):
			clone.__dict__[key] = self.__dict__[key]
		return clone

	def frozen_clone(self):
		clone = self.clone()
		clone.frozen = True
		return clone

	def stop_if_frozen(self):
		if self.frozen: raise FrozenException('Cannot modify datastructure while it is frozen')

