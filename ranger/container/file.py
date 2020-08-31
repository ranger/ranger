# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import re

from ranger import PY3
from ranger.container.fsobject import FileSystemObject

N_FIRST_BYTES = 256
CONTROL_CHARACTERS = set(list(range(0, 9)) + list(range(14, 32)))
if not PY3:
    CONTROL_CHARACTERS = set(chr(n) for n in CONTROL_CHARACTERS)

# Don't even try to preview files which match this regular expression:
PREVIEW_BLACKLIST = re.compile(r"""
        # look at the extension:
        \.(
            # one character extensions:
                [oa]
            # media formats:
                | avi | mpe?g | mp\d | og[gmv] | wm[av] | mkv | flv
                | vob | wav | mpc | flac | divx? | xcf | pdf
            # binary files:
                | torrent | class | so | img | py[co] | dmg
        )
        # ignore filetype-independent suffixes:
            (\.part|\.bak|~)?
        # ignore fully numerical file extensions:
            (\.\d+)*?
        $
""", re.VERBOSE | re.IGNORECASE)  # pylint: disable=no-member

# Preview these files (almost) always:
PREVIEW_WHITELIST = re.compile(r"""
        \.(
            txt | py | c
        )
        # ignore filetype-independent suffixes:
            (\.part|\.bak|~)?
        $
""", re.VERBOSE | re.IGNORECASE)  # pylint: disable=no-member


class File(FileSystemObject):
    is_file = True
    preview_data = None
    preview_known = False
    preview_loading = False
    _firstbytes = None

    @property
    def firstbytes(self):
        if self._firstbytes is not None:
            return self._firstbytes
        try:
            with open(self.path, 'rb') as fobj:
                self._firstbytes = set(fobj.read(N_FIRST_BYTES))
        # IOError for Python2, OSError for Python3
        except (IOError, OSError):
            return None
        return self._firstbytes

    def is_binary(self):
        if self.firstbytes and CONTROL_CHARACTERS & self.firstbytes:
            return True
        return False

    def has_preview(self):  # pylint: disable=too-many-return-statements
        if not self.fm.settings.preview_files:
            return False
        if self.is_socket or self.is_fifo or self.is_device:
            return False
        if not self.accessible:
            return False
        if self.fm.settings.preview_max_size and \
                self.size > self.fm.settings.preview_max_size:
            return False
        if self.fm.settings.preview_script and \
                self.fm.settings.use_preview_script:
            return True
        if self.container:
            return False
        if PREVIEW_WHITELIST.search(self.basename):
            return True
        if PREVIEW_BLACKLIST.search(self.basename):
            return False
        if self.path == '/dev/core' or self.path == '/proc/kcore':
            return False
        if self.is_binary():
            return False
        return True

    def get_preview_source(self, width, height):
        return self.fm.get_preview(self, width, height)

    def is_image_preview(self):
        try:
            return self.fm.previews[self.realpath]['imagepreview']
        except KeyError:
            return False

    def __eq__(self, other):
        return isinstance(other, File) and self.path == other.path

    def __neq__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.path)
