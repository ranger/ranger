# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""A console file manager with VI key bindings.

It provides a minimalistic and nice curses interface with a view on the
directory hierarchy.  The secondary task of ranger is to figure out which
program you want to use to open your files with.
"""

from __future__ import (absolute_import, print_function)

import sys
import os

# Information
__license__ = 'GPL3'
__version__ = '1.8.1'
__author__ = __maintainer__ = 'Roman Zimbelmann'
__email__ = 'hut@hut.pm'

# Constants
RANGERDIR = os.path.dirname(__file__)
TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200
MAX_RESTORABLE_TABS = 3
MACRO_DELIMITER = '%'
DEFAULT_PAGER = 'less'
CACHEDIR = os.path.expanduser("~/.cache/ranger")
USAGE = '%prog [options] [path]'
VERSION = 'ranger-master %s\n\nPython %s' % (__version__, sys.version)


# If the environment variable XDG_CONFIG_HOME is non-empty, CONFDIR is ignored
# and the configuration directory will be $XDG_CONFIG_HOME/ranger instead.
CONFDIR = '~/.config/ranger'

args = None  # pylint: disable=invalid-name

from ranger.core.main import main  # NOQA pylint: disable=wrong-import-position
