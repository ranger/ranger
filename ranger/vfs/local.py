# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""
An abstraction layer over the local file system
"""

from stat import S_IFDIR, S_IFREG, S_IFCHR, S_IFBLK, S_IFIFO, S_IFSOCK, S_ISLNK
from os import lstat
from os.path import abspath, isdir

from ranger.vfs import Metadata, UNUSABLE, ValueInvalid

try:
    from stat import filemode
except ImportError:
    # stat.filemode was introduced in python3.3
    from ranger.ext.filemode import filemode

class LocalFile(object):
    def __init__(self, path):
        self.path = abspath(path)
        self.metadata = Metadata()

    def load_basic_metadata(self):
        # Obtain metadata
        path = self.path
        meta = self.metadata
        is_link = False
        try:
            stat = stat(path)
            if S_ISLNK(stat.st_mode):
                is_link = True
                stat = lstat(path)
        except OSError:
            is_link = ValueInvalid

        # Fill the Metadata object with relevant data
        meta.refresh()  # clears extended metadata too
        meta.path = path
        meta.permission_mode = stat.st_mode
        meta.is_link = is_link
        meta.filetype = self._get_file_type(stat.st_mode)

    def load_all_metadata(self):
        self.load_basic_metadata()

    def _get_file_type(self, mode=None):
        if mode is None:
            mode = self.metadata.permission_mode
            if mode in UNUSABLE:
                return 'unknown'

        # See "stat.py" of python standard library
        filetype = mode & 0o170000
        if filetype == S_IFDIR:
            return 'directory'
        if filetype == S_IFREG:
            return 'file'
        if filetype in (S_IFCHR, S_IFBLK):
            return 'device'
        if filetype == S_IFIFO:
            return 'fifo'
        if filetype == S_IFSOCK:
            return 'socket'
        return 'unknown'

    def get_permission_string(self):
        return filemode(self.metadata.permission_mode)
