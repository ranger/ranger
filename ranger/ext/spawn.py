# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from subprocess import Popen, PIPE, CalledProcessError
ENCODING = 'utf-8'


def spawn(*args, **kwargs):
    """Runs a program, waits for its termination and returns its stdout

    This function is similar to python 2.7's subprocess.check_output,
    but is favored due to python 2.6 compatibility.

    The arguments may be:

        spawn(string)
        spawn(command, arg1, arg2...)
        spawn([command, arg1, arg2])

    The string will be run through a shell, otherwise the command is executed
    directly.

    The keyword argument "decode" determines if the output shall be decoded
    with the encoding '%s'.

    Further keyword arguments are passed to Popen.
    """ % (ENCODING, )

    if len(args) == 1:
        popen_arguments = args[0]
        shell = isinstance(popen_arguments, str)
    else:
        popen_arguments = args
        shell = False

    if 'decode' in kwargs:
        do_decode = kwargs['decode']
        del kwargs['decode']
    else:
        do_decode = True
    if 'stdout' not in kwargs:
        kwargs['stdout'] = PIPE
    if 'shell' not in kwargs:
        kwargs['shell'] = shell

    process = Popen(popen_arguments, **kwargs)
    stdout, stderr = process.communicate()
    return_value = process.poll()
    if return_value:
        error = CalledProcessError(return_value, popen_arguments[0])
        error.output = stdout
        raise error

    if do_decode:
        return stdout.decode(ENCODING)
    else:
        return stdout
