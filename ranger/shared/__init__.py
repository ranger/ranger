class Awareness(object):
	pass

from .mimetype import MimeTypeAware
from .settings import SettingsAware

class EnvironmentAware(Awareness):
   env = None

class FileManagerAware(Awareness):
   fm = None
