"""FileSystemObjects are representation of files and directories"""

BAD_INFO = '?'

# So they can be imported from other files more easily:
from .fsobject import FileSystemObject
from .file import File
from .directory import Directory
