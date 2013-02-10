# Copyright (C) 2012  Roman Zimbelmann <romanz@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

import os
import subprocess

def Popen_forked(*args, **kwargs):
    """
    Forks process and runs Popen with the given args and kwargs.

    If os.fork() is not supported, runs Popen without forking and returns the
    process object returned by Popen.
    Otherwise, returns None.
    """
    try:
        pid = os.fork()
    except:
        # fall back to not forking if os.fork() is not supported
        return subprocess.Popen(*args, **kwargs)
    else:
        if pid == 0:
            os.setsid()
            kwargs['stdin'] = open(os.devnull, 'r')
            kwargs['stdout'] = kwargs['stderr'] = open(os.devnull, 'w')
            subprocess.Popen(*args, **kwargs)
            os._exit(0)
