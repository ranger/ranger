# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from stat import S_IXOTH, S_IFREG
from ranger.ext.iter_tools import unique
from os import listdir, environ, stat


_cached_executables = None


def get_executables():
    """Return all executable files in $PATH. Cached version."""
    global _cached_executables
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
        except Exception:
            continue
        for item in content:
            abspath = path + '/' + item
            try:
                filestat = stat(abspath)
            except Exception:
                continue
            if filestat.st_mode & (S_IXOTH | S_IFREG):
                executables.add(item)
    return executables
