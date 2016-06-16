# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from os.path import realpath, abspath, dirname, ismount


def mount_path(path):
    """Get the mount root of a directory"""
    path = abspath(realpath(path))
    while path != '/':
        if ismount(path):
            return path
        path = dirname(path)
    return '/'
