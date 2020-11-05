# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""VCS Extension"""

from __future__ import (absolute_import, division, print_function)

from .vcs import Vcs, VcsError, VcsThread

__all__ = ['Vcs', 'VcsError', 'VcsThread']
