# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

import os
import subprocess


def Popen_forked(*args, **kwargs):
    """Forks process and runs Popen with the given args and kwargs.

    Returns True if forking succeeded, otherwise False.
    """
    try:
        pid = os.fork()
    except OSError:
        return False
    if pid == 0:
        os.setsid()
        kwargs['stdin'] = open(os.devnull, 'r')
        kwargs['stdout'] = kwargs['stderr'] = open(os.devnull, 'w')
        subprocess.Popen(*args, **kwargs)
        os._exit(0)
    else:
        os.wait()
    return True
