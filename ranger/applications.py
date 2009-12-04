ALLOWED_FLAGS = 'sdpSDP'

class Applications(object):
	def get(self, app):
		try:
			return getattr(self, 'app_' + app)
		except AttributeError:
			return self.app_default

	def has(self, app):
		return hasattr(self, 'app_' + app)

	def all(self):
		return [x for x in self.__dict__ if x.startswith('app_')]

