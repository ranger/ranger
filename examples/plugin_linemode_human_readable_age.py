"""Human-readable file age using humanize library"""

from __future__ import (absolute_import, division, print_function)

from datetime import datetime
import humanize

import ranger.api
from ranger.core.linemode import LinemodeBase
from ranger.core.shared import FileManagerAware


@ranger.api.register_linemode
class AgeLinemode(LinemodeBase, FileManagerAware):
    """Implements an age linemode for ranger"""
    name = "age"

    def __init__(self):
        self.fm.execute_console("map Ma linemode age")

    def filetitle(self, fobj, metadata):
        return fobj.relative_path

    def infostring(self, fobj, metadata):
        if fobj.stat is None:
            return '?'
        now = datetime.now()
        mtime = datetime.fromtimestamp(fobj.stat.st_mtime)
        if now < mtime:
            # indicate future dates & show without precision loss
            return '-' + humanize.naturaldelta(mtime - now)

        return humanize.naturaldelta(now - mtime)
