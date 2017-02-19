# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""A console file manager with VI key bindings.

It provides a minimalistic and nice curses interface with a view on the
directory hierarchy.  The secondary task of ranger is to figure out which
program you want to use to open your files with.
"""

from __future__ import (absolute_import, division, print_function)

import os

# Information
__license__ = 'GPL3'
__version__ = '1.9.0b5'
__author__ = __maintainer__ = 'Roman Zimbelmann'
__email__ = 'hut@hut.pm'

# Constants
RANGERDIR = os.path.dirname(__file__)
TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200
MAX_RESTORABLE_TABS = 3
MACRO_DELIMITER = '%'
MACRO_DELIMITER_ESC = '%%'
DEFAULT_PAGER = 'less'
USAGE = '%prog [options] [path]'
VERSION = 'ranger-master {0}'.format(__version__)


# These variables are ignored if the corresponding
# XDG environment variable is non-empty and absolute
CACHEDIR = os.path.expanduser('~/.cache/ranger')
CONFDIR = os.path.expanduser('~/.config/ranger')
DATADIR = os.path.expanduser('~/.local/share/ranger')

args = None  # pylint: disable=invalid-name

from ranger.core.main import main  # NOQA pylint: disable=wrong-import-position
