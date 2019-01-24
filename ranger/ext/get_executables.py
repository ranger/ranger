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
    term = environ.get('TERMCMD', environ['TERM'])

    # Handle aliases of xterm and urxvt, rxvt and st and
    # termite
    # Match 'xterm', 'xterm-256color'
    if term in ['xterm', 'xterm-256color']:
        term = 'xterm'
    if term in ['xterm-kitty']:
        term = 'kitty'
    if term in ['xterm-termite']:
        term = 'termite'
    if term in ['st', 'st-256color']:
        term = 'st'
    if term in ['urxvt', 'rxvt-unicode',
                'rxvt-unicode-256color']:
        term = 'urxvt'
    if term in ['rxvt', 'rxvt-256color']:
        if 'rxvt' in get_executables():
            term = 'rxvt'
        else:
            term = 'urxvt'

    if shlex.split(term)[0] not in get_executables():
        term = 'x-terminal-emulator'
        if term not in get_executables():
            term = 'xterm'
    return term
