# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, print_function)

import re
from ranger.container.fsobject import FileSystemObject

N_FIRST_BYTES = 256
# pylint: disable=invalid-name
control_characters = set(chr(n) for n in set(range(0, 9)) | set(range(14, 32)))
# pylint: enable=invalid-name

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

    _linemode = "filename"
    _firstbytes = None

    @property
    def firstbytes(self):
        if self._firstbytes is None:
            try:
                fobj = open(self.path, 'r')
                self._firstbytes = fobj.read(N_FIRST_BYTES)
                fobj.close()
                return self._firstbytes
            except Exception:
                pass
        else:
            return self._firstbytes

    def is_binary(self):
        if self.firstbytes and control_characters & set(self.firstbytes):
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
