# From http://blog.pythonisito.com/2008/08/lazy-descriptors.html

class lazy_property(object):
	"""
	A @property-like decorator with lazy evaluation

	Example:
	class Foo:
		@lazy_property
			def bar(self):
				result = [...]
				return result
	"""

	def __init__(self, method):
		self._method = method
		self.__name__ = method.__name__
		self.__doc__ = method.__doc__

	def __get__(self, obj, cls=None):
		if obj is None:  # to fix issues with pydoc
			return None
		result = self._method(obj)
		obj.__dict__[self.__name__] = result
		return result
