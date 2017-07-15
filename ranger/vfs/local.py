# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""
An abstraction layer for the local file system
"""

import os
from os.path import abspath
from stat import (S_IFDIR, S_IFREG, S_IFCHR, S_IFBLK, S_IFIFO, S_IFSOCK, S_ISLNK)

from ranger.ext.human_readable import human_readable
from ranger.vfs import (Metadata, UNUSABLE, ValueUnknown, ValueNotApplicable,
                        cache_until_outdated, BaseFile)

try:
    from stat import filemode
except ImportError:
    # stat.filemode was introduced in python3.3
    from ranger.ext.filemode import filemode


class LocalFile(BaseFile):
    def __init__(self, path):
        BaseFile.__init__(self)
        self.path = abspath(path)

        self._cached_permission_string_time = -1
        self._cached_permission_string = None
        self._cached_info_string_time = -1
        self._cached_info_string = None

    def load_basic_metadata(self):
        path = self.path
        meta = self.metadata

        # Make sure to override these fields in all if-branches, if applicable
        file_exists = ValueNotApplicable
        filetype = ValueNotApplicable
        is_link = ValueNotApplicable
        link_target_exists = ValueNotApplicable
        size = ValueNotApplicable
        st_atime = ValueNotApplicable
        st_ctime = ValueNotApplicable
        st_mode = ValueNotApplicable
        st_mtime = ValueNotApplicable
        st_size = ValueNotApplicable

        # Get os.stat() of the file, dealing with links
        try:
            stat = os.lstat(path)
        except OSError:
            file_exists = False
            # Use the fallback values from above, "ValueNotApplicable" for all
        else:
            file_exists = True
            if S_ISLNK(stat.st_mode):
                is_link = True
                try:
                    stat = os.stat(path)
                except OSError:
                    # Link target does not exist.  That's ok, we will simply
                    # display the info of the link rather than of the target.
                    link_target_exists = False
                else:
                    link_target_exists = True
            else:
                is_link = False
            st_mode = stat.st_mode
            st_atime = stat.st_atime
            st_ctime = stat.st_ctime
            st_mtime = stat.st_mtime
            st_size = stat.st_size

        # Set derived data
        filetype = self._get_file_type(st_mode)
        if filetype == 'file':
            size = st_size
        elif filetype == 'directory':
            size = ValueUnknown  # number of files in dir; fetch when needed

        # Fill the Metadata object with relevant data
        meta.refresh()  # clears extended metadata too
        meta.file_exists = file_exists
        meta.filetype = filetype
        meta.is_link = is_link
        meta.link_target_exists = link_target_exists
        meta.path = path
        meta.size = size
        meta.st_atime = st_atime
        meta.st_ctime = st_ctime
        meta.st_mode = st_mode
        meta.st_mtime = st_mtime
        meta.st_size = st_size

    def load_all_metadata(self):
        self.load_basic_metadata()

    def _get_file_type(self, mode=None):
        if mode is None:
            mode = self.metadata.st_mode
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

    @cache_until_outdated
    def get_permission_string(self):
        return filemode(self.metadata.st_mode)

    @cache_until_outdated
    def get_info_string(self):
        meta = self.metadata
        filetype = meta.filetype
        infostring = 'n/a'
        if filetype in UNUSABLE:
            pass
        elif filetype == 'file':
            if meta.st_size not in UNUSABLE:
                infostring = ' ' + human_readable(meta.st_size)
        elif filetype == 'directory':
            pass
        else:
            infostring = filetype
        if meta.is_link is True:
            infostring = '-> ' + infostring

        return infostring
