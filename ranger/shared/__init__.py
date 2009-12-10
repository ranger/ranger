class Awareness(object):
	pass

class EnvironmentAware(Awareness):
   env = None

class FileManagerAware(Awareness):
   fm = None

from .mimetype import MimeTypeAware
from .settings import SettingsAware
