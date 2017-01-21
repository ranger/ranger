# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Functions to escape metacharacters of arguments for shell commands."""

from __future__ import (absolute_import, division, print_function)


META_CHARS = (' ', "'", '"', '`', '&', '|', ';', '#',
              '$', '!', '(', ')', '[', ']', '<', '>', '\t')
UNESCAPABLE = set(map(chr, list(range(9)) + list(range(10, 32)) + list(range(127, 256))))
META_DICT = dict([(mc, '\\' + mc) for mc in META_CHARS])


def shell_quote(string):
    """Escapes by quoting"""
    return "'" + str(string).replace("'", "'\\''") + "'"


def shell_escape(arg):
    """Escapes by adding backslashes"""
    arg = str(arg)
    if UNESCAPABLE & set(arg):
        return shell_quote(arg)
    arg = arg.replace('\\', '\\\\')  # make sure this comes at the start
    for key, value in META_DICT.items():
        arg = arg.replace(key, value)
    return arg
