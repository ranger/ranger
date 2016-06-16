# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from subprocess import Popen, PIPE
ENCODING = 'utf-8'


def spawn(*args):
    """Runs a program, waits for its termination and returns its stdout"""
    if len(args) == 1:
        popen_arguments = args[0]
        shell = isinstance(popen_arguments, str)
    else:
        popen_arguments = args
        shell = False
    process = Popen(popen_arguments, stdout=PIPE, shell=shell)
    stdout, stderr = process.communicate()
    return stdout.decode(ENCODING)
