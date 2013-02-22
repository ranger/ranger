# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

from os.path import realpath, abspath, dirname, ismount

def mount_path(path):
    """Get the mount root of a directory"""
    path = abspath(realpath(path))
    while path != '/':
        if ismount(path):
            return path
        path = dirname(path)
    return '/'
