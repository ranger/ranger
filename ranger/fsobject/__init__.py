"""FileSystemObjects are representation of files and directories
with fast access to their properties through caching"""

T_FILE = 'file'
T_DIRECTORY = 'directory'
T_UNKNOWN = 'unknown'
T_NONEXISTANT = 'nonexistant'

BAD_INFO = None

class NotLoadedYet(Exception):
	pass

from ranger.fsobject.file import File
from ranger.fsobject.directory import Directory, NoDirectoryGiven
from ranger.fsobject.fsobject import FileSystemObject
