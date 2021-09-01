# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import os
from io import open
from subprocess import Popen


def Popen_forked(*args, **kwargs):  # pylint: disable=invalid-name
    """Forks process and runs Popen with the given args and kwargs.

    Returns True if forking succeeded, otherwise False.
    """
    try:
        pid = os.fork()
    except OSError:
        return False
    if pid == 0:
        os.setsid()
        with open(os.devnull, 'r', encoding="utf-8") as null_r, open(
            os.devnull, 'w', encoding="utf-8"
        ) as null_w:
            kwargs['stdin'] = null_r
            kwargs['stdout'] = kwargs['stderr'] = null_w
            Popen(*args, **kwargs)  # pylint: disable=consider-using-with
        os._exit(0)  # pylint: disable=protected-access
    else:
        os.wait()
    return True
