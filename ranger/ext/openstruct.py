class OpenStruct(object):
	def __init__(self, __dictionary=None, **__keywords):
		if __dictionary:
			self.__dict__.update(__dictionary)
		if __keywords:
			self.__dict__.update(__keywords)

	def __getitem__(self, key):
		return self.__dict__[key]
	
	def __setitem__(self, key, value):
		self.__dict__[key] = value
		return value

	def __contains__(self, key):
		return key in self.__dict__
