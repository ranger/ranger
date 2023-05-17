# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import absolute_import

from contextlib import contextmanager

from subprocess import Popen

try:
    from ranger import PY3
except ImportError:
    from sys import version_info
    PY3 = version_info[0] >= 3

if PY3:
    # pylint: disable=ungrouped-imports,unused-import
    from subprocess import DEVNULL
else:
    import os
    # pylint: disable=consider-using-with
    DEVNULL = open(os.devnull, "wb")


# COMPAT: Python 2 (and Python <=3.2) subprocess.Popen objects aren't
#         context managers. We don't care about early Python 3 but we do want
#         to wrap Python 2's Popen. There's no harm in always using this Popen
#         but it is only necessary when used with with-statements. This can be
#         removed once we ditch Python 2 support.
@contextmanager
def Popen23(*args, **kwargs):  # pylint: disable=invalid-name
    if PY3:
        yield Popen(*args, **kwargs)
        return
    else:
        popen2 = Popen(*args, **kwargs)
    try:
        yield popen2
    finally:
        # From Lib/subprocess.py Popen.__exit__:
        if popen2.stdout:
            popen2.stdout.close()
        if popen2.stderr:
            popen2.stderr.close()
        try:  # Flushing a BufferedWriter may raise an error
            if popen2.stdin:
                popen2.stdin.close()
        finally:
            # Wait for the process to terminate, to avoid zombies.
            popen2.wait()
