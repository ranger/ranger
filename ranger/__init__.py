# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""A console file manager with VI key bindings.

It provides a minimalistic and nice curses interface with a view on the
directory hierarchy.  The secondary task of ranger is to figure out which
program you want to use to open your files with.
"""

import sys
import os
import tempfile

# Information
__license__ = 'GPL3'
__version__ = '1.7.2'
__author__ = __maintainer__ = 'Roman Zimbelmann'
__email__ = 'hut@hut.pm'

# The oldest compatible config versions
required_configs = {
    'scope.sh': "1.7.999-2015-11-16",
    'commands.py': "1.7.2.999-2015-11-16",
    'rifle.conf': "1.7.2.999-2015-11-16",
    'rc.conf': "1.7.2.999-2015-11-16",
}

# Constants
RANGERDIR = os.path.dirname(__file__)
TICKS_BEFORE_COLLECTING_GARBAGE = 100
TIME_BEFORE_FILE_BECOMES_GARBAGE = 1200
MAX_RESTORABLE_TABS = 3
MACRO_DELIMITER = '%'
DEFAULT_PAGER = 'less'
LOGFILE = tempfile.gettempdir()+'/ranger_errorlog'
CACHEDIR = os.path.expanduser("~/.cache/ranger")
USAGE = '%prog [options] [path]'
VERSION = 'ranger-master %s\n\nPython %s' % (__version__, sys.version)

# If the environment variable XDG_CONFIG_HOME is non-empty, CONFDIR is ignored
# and the configuration directory will be $XDG_CONFIG_HOME/ranger instead.
CONFDIR = '~/.config/ranger'

# Debugging functions.  These will be activated when run with --debug.
# Example usage in the code:
# import ranger; ranger.log("hello world")
def log(*objects, **keywords):
    """Writes objects to a logfile (for the purpose of debugging only.)
    Has the same arguments as print() in python3.
    """
    from ranger import arg
    if LOGFILE is None or not arg.debug or arg.clean: return
    start = keywords.get('start', 'ranger:')
    sep   = keywords.get('sep', ' ')
    end   = keywords.get('end', '\n')
    _file = keywords['file'] if 'file' in keywords else open(LOGFILE, 'a')
    _file.write(sep.join(map(str, (start, ) + objects)) + end)


def log_traceback():
    from ranger import arg
    if LOGFILE is None or not arg.debug or arg.clean: return
    import traceback
    traceback.print_stack(file=open(LOGFILE, 'a'))

from ranger.core.main import main
