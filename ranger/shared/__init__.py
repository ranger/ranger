"""Shared objects contian singleton variables wich can be
inherited, essentially acting like global variables."""
class Awareness(object):
	pass

class EnvironmentAware(Awareness):
   env = None

class FileManagerAware(Awareness):
   fm = None

from .mimetype import MimeTypeAware
from .settings import SettingsAware
