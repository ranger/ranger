import os, sys

__all__ = [ x[0:x.index('.')] \
		for x in os.listdir(os.path.dirname(__file__)) \
		if x.startswith('tc_') ]

def init():
	sys.path.append(os.path.abspath(os.path.join(sys.path[0], '..')))

class Fake(object):
	def __getattr__(self, attrname):
		if not hasattr(self, attrname):
			setattr(self, attrname, Fake())
		return self.__dict__[attrname]

	def __call__(self, *_):
		return Fake()

	def __clear__(self):
		self.__dict__.clear()

	def __iter__(self):
		return iter(())

class OK(Exception):
	pass

def raise_ok(*_, **__):
	raise OK()
