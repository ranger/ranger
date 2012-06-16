# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

"""
A console file manager with VI key bindings.

It provides a minimalistic and nice curses interface with a view on the
directory hierarchy.  The secondary task of ranger is to figure out which
program you want to use to open your files with.
"""

import os

# Information
__license__ = 'GPL3'
__version__ = '1.5.4'
__author__ = __maintainer__ = 'Roman Zimbelmann'
__email__ = 'romanz@lavabit.com'

# Constants
RANGERDIR = os.path.dirname(__file__)
TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200
MACRO_DELIMITER = '%'
DEFAULT_PAGER = 'less'
LOGFILE = '/tmp/ranger_errorlog'
USAGE = '%prog [options] [path/filename]'
VERSION = 'ranger-git based on %s' % __version__

# If the environment variable XDG_CONFIG_HOME is non-empty, CONFDIR is ignored
# and the configuration directory will be $XDG_CONFIG_HOME/ranger instead.
CONFDIR = '~/.config/ranger'

from ranger.core.main import main
