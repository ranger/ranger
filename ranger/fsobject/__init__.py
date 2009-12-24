"""FileSystemObjects are representation of files and directories
with fast access to their properties through caching"""

T_FILE = 'file'
T_DIRECTORY = 'directory'
T_UNKNOWN = 'unknown'
T_NONEXISTANT = 'nonexistant'

BAD_INFO = None

class NotLoadedYet(Exception):
	pass

from .fsobject import FileSystemObject
from .file import File
from .directory import Directory, NoDirectoryGiven
from .loader import Loader
