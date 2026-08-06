# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import absolute_import

try:
    from ranger import PY3
except ImportError:
    from sys import version_info
    PY3 = version_info[0] >= 3


def create_string_io(content):
    if PY3:
        from io import StringIO
    else:
        from StringIO import StringIO  # pylint: disable=import-error

    return StringIO(content)
