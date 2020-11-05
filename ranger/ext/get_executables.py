# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from stat import S_IXOTH, S_IFREG
from os import listdir, environ, stat
import shlex

from ranger.ext.iter_tools import unique


_cached_executables = None  # pylint: disable=invalid-name


def get_executables():
    """Return all executable files in $PATH. Cached version."""
    global _cached_executables  # pylint: disable=global-statement,invalid-name
    if _cached_executables is None:
        _cached_executables = get_executables_uncached()
    return _cached_executables


def get_executables_uncached(*paths):
    """Return all executable files in each of the given directories.

    Looks in $PATH by default.
    """
    if not paths:
        try:
            pathstring = environ['PATH']
        except KeyError:
            return ()
        paths = unique(pathstring.split(':'))

    executables = set()
    for path in paths:
        try:
            content = listdir(path)
        except OSError:
            continue
        for item in content:
            abspath = path + '/' + item
            try:
                filestat = stat(abspath)
            except OSError:
                continue
            if filestat.st_mode & (S_IXOTH | S_IFREG):
                executables.add(item)
    return executables


def get_term():
    """Get the user terminal executable name.

    Either $TERMCMD, $TERM, "x-terminal-emulator" or "xterm", in this order.
    """
    command = environ.get('TERMCMD', environ.get('TERM'))
    if shlex.split(command)[0] not in get_executables():
        command = 'x-terminal-emulator'
        if command not in get_executables():
            command = 'xterm'
    return command
