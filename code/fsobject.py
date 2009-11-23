class FrozenException(Exception): pass
class NotLoadedYet(Exception): pass

class FSObject(object):
	def __init__(self, path):
		self.path = path
		self.exists = False
		self.accessible = False
		self.marked = False
		self.tagged = False
		self.frozen = False
		self.loaded = False
		self.stat = None

	def clone(self):
		clone = type(self)(self.path)
		for key in iter(self.__dict__):
			clone.__dict__[key] = self.__dict__[key]
		return clone

	def load(self):
		self.stop_if_frozen()
		self.loaded = True

		import os
		try:
			self.stat = os.stat(self.path)
			self.exists = True
			self.accessible = True
		except OSError:
			self.exists = False
			self.accessible = False

	def load_once(self):
		self.stop_if_frozen()
		if not self.loaded: self.load()

	def load_if_outdated(self):
		self.stop_if_frozen()
		import os

		if not self.loaded:
			self.load()
			return True

		real_mtime = os.stat(self.path).st_mtime
		cached_mtime = self.stat.st_mtime

		if real_mtime != cached_mtime:
			self.load()
			return True

		return False

	def frozen_clone(self):
		self.stop_if_frozen()
		return self.clone().freeze()

	def stop_if_frozen(self):
		if self.frozen: raise FrozenException()

	def freeze(self):
		self.frozen = True
		return self

