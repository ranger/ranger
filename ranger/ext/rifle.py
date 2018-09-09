#!/usr/bin/python
# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""rifle, the file executor/opener of ranger

This can be used as a standalone program or can be embedded in python code.
When used together with ranger, it doesn't have to be installed to $PATH.

Example usage:

    rifle = Rifle("rifle.conf")
    rifle.reload_config()
    rifle.execute(["file1", "file2"])
"""

from __future__ import (absolute_import, division, print_function)

import os.path
import re
from subprocess import Popen, PIPE
import sys

__version__ = 'rifle 1.9.2'

# Options and constants that a user might want to change:
DEFAULT_PAGER = 'less'
DEFAULT_EDITOR = 'vim'
ASK_COMMAND = 'ask'
ENCODING = 'utf-8'

# Imports from ranger library, plus reimplementations in case ranger is not
# installed so rifle can be run as a standalone program.
try:
    from ranger.ext.get_executables import get_executables
except ImportError:
    _CACHED_EXECUTABLES = None

    def get_executables():
        """Return all executable files in $PATH + Cache them."""
        global _CACHED_EXECUTABLES  # pylint: disable=global-statement
        if _CACHED_EXECUTABLES is not None:
            return _CACHED_EXECUTABLES

        if 'PATH' in os.environ:
            paths = os.environ['PATH'].split(':')
        else:
            paths = ['/usr/bin', '/bin']

        from stat import S_IXOTH, S_IFREG
        paths_seen = set()
        _CACHED_EXECUTABLES = set()
        for path in paths:
            if path in paths_seen:
                continue
            paths_seen.add(path)
            try:
                content = os.listdir(path)
            except OSError:
                continue
            for item in content:
                abspath = path + '/' + item
                try:
                    filestat = os.stat(abspath)
                except OSError:
                    continue
                if filestat.st_mode & (S_IXOTH | S_IFREG):
                    _CACHED_EXECUTABLES.add(item)
        return _CACHED_EXECUTABLES


try:
    from ranger.ext.popen_forked import Popen_forked
except ImportError:
    def Popen_forked(*args, **kwargs):  # pylint: disable=invalid-name
        """Forks process and runs Popen with the given args and kwargs."""
        try:
            pid = os.fork()
        except OSError:
            return False
        if pid == 0:
            os.setsid()
            kwargs['stdin'] = open(os.devnull, 'r')
            kwargs['stdout'] = kwargs['stderr'] = open(os.devnull, 'w')
            Popen(*args, **kwargs)
            os._exit(0)  # pylint: disable=protected-access
        return True


def _is_terminal():
    # Check if stdin (file descriptor 0), stdout (fd 1) and
    # stderr (fd 2) are connected to a terminal
    try:
        os.ttyname(0)
        os.ttyname(1)
        os.ttyname(2)
    except OSError:
        return False
    return True


def squash_flags(flags):
    """Remove lowercase flags if the respective uppercase flag exists

    >>> squash_flags('abc')
    'abc'
    >>> squash_flags('abcC')
    'ab'
    >>> squash_flags('CabcAd')
    'bd'
    """
    exclude = ''.join(f.upper() + f.lower() for f in flags if f == f.upper())
    return ''.join(f for f in flags if f not in exclude)


class Rifle(object):  # pylint: disable=too-many-instance-attributes
    delimiter1 = '='
    delimiter2 = ','

    # TODO: Test all of the hooks properly
    def hook_before_executing(self, command, mimetype, flags):
        pass

    def hook_after_executing(self, command, mimetype, flags):
        pass

    @staticmethod
    def hook_command_preprocessing(command):
        return command

    @staticmethod
    def hook_command_postprocessing(command):
        return command

    @staticmethod
    def hook_environment(env):
        return env

    @staticmethod
    def hook_logger(string):
        sys.stderr.write(string + "\n")

    def __init__(self, config_file):
        self.config_file = config_file
        self._app_flags = ''
        self._app_label = None
        self._initialized_mimetypes = False
        self._mimetype = None
        self._skip = None
        self.rules = None

        # get paths for mimetype files
        self._mimetype_known_files = [os.path.expanduser("~/.mime.types")]
        if __file__.endswith("ranger/ext/rifle.py"):
            # Add ranger's default mimetypes when run from ranger directory
            self._mimetype_known_files.append(
                __file__.replace("ext/rifle.py", "data/mime.types"))

    def reload_config(self, config_file=None):
        """Replace the current configuration with the one in config_file"""
        if config_file is None:
            config_file = self.config_file
        fobj = open(config_file, 'r')
        self.rules = []
        lineno = 0
        for line in fobj:
            lineno += 1
            line = line.strip()
            if line.startswith('#') or line == '':
                continue
            if self.delimiter1 not in line:
                raise ValueError("Line without delimiter")
            tests, command = line.split(self.delimiter1, 1)
            tests = tests.split(self.delimiter2)
            tests = tuple(tuple(f.strip().split(None, 1)) for f in tests)
            command = command.strip()
            self.rules.append((command, tests))
        fobj.close()

    def _eval_condition(self, condition, files, label):
        # Handle the negation of conditions starting with an exclamation mark,
        # then pass on the arguments to _eval_condition2().

        if not condition:
            return True
        if condition[0].startswith('!'):
            new_condition = tuple([condition[0][1:]]) + tuple(condition[1:])
            return not self._eval_condition2(new_condition, files, label)
        return self._eval_condition2(condition, files, label)

    def _eval_condition2(  # pylint: disable=too-many-return-statements,too-many-branches
            self, rule, files, label):
        # This function evaluates the condition, after _eval_condition() handled
        # negation of conditions starting with a "!".

        if not files:
            return False

        function = rule[0]
        argument = rule[1] if len(rule) > 1 else ''

        if function == 'ext':
            if os.path.isfile(files[0]):
                partitions = os.path.basename(files[0]).rpartition('.')
                if not partitions[0]:
                    return False
                return bool(re.search('^(' + argument + ')$', partitions[2].lower()))
        elif function == 'name':
            return bool(re.search(argument, os.path.basename(files[0])))
        elif function == 'match':
            return bool(re.search(argument, files[0]))
        elif function == 'file':
            return os.path.isfile(files[0])
        elif function == 'directory':
            return os.path.isdir(files[0])
        elif function == 'path':
            return bool(re.search(argument, os.path.abspath(files[0])))
        elif function == 'mime':
            return bool(re.search(argument, self.get_mimetype(files[0])))
        elif function == 'has':
            if argument.startswith("$"):
                if argument[1:] in os.environ:
                    return os.environ[argument[1:]] in get_executables()
                return False
            else:
                return argument in get_executables()
        elif function == 'terminal':
            return _is_terminal()
        elif function == 'number':
            if argument.isdigit():
                self._skip = int(argument)
            return True
        elif function == 'label':
            self._app_label = argument
            if label:
                return argument == label
            return True
        elif function == 'flag':
            self._app_flags = argument
            return True
        elif function == 'X':
            return sys.platform == 'darwin' or 'DISPLAY' in os.environ
        elif function == 'env':
            return bool(os.environ.get(argument))
        elif function == 'else':
            return True
        return None

    def get_mimetype(self, fname):
        # Spawn "file" to determine the mime-type of the given file.
        if self._mimetype:
            return self._mimetype

        import mimetypes
        for path in self._mimetype_known_files:
            if path not in mimetypes.knownfiles:
                mimetypes.knownfiles.append(path)
        self._mimetype, _ = mimetypes.guess_type(fname)

        if not self._mimetype:
            process = Popen(["file", "--mime-type", "-Lb", fname], stdout=PIPE, stderr=PIPE)
            mimetype, _ = process.communicate()
            self._mimetype = mimetype.decode(ENCODING).strip()
            if self._mimetype == 'application/octet-stream':
                try:
                    process = Popen(["mimetype", "--output-format", "%m", fname],
                                    stdout=PIPE, stderr=PIPE)
                    mimetype, _ = process.communicate()
                    self._mimetype = mimetype.decode(ENCODING).strip()
                except OSError:
                    pass
        return self._mimetype

    def _build_command(self, files, action, flags):
        # Get the flags
        if isinstance(flags, str):
            self._app_flags += flags
        self._app_flags = squash_flags(self._app_flags)
        filenames = "' '".join(f.replace("'", "'\\\''") for f in files if "\x00" not in f)
        return "set -- '%s'; %s" % (filenames, action)

    def list_commands(self, files, mimetype=None):
        """List all commands that are applicable for the given files

        Returns one 4-tuple for all currently applicable commands
        The 4-tuple contains (count, command, label, flags).
        count is the index, counted from 0 upwards,
        command is the command that will be executed.
        label and flags are the label and flags specified in the rule.
        """
        self._mimetype = mimetype
        count = -1
        for cmd, tests in self.rules:
            self._skip = None
            self._app_flags = ''
            self._app_label = None
            for test in tests:
                if not self._eval_condition(test, files, None):
                    break
            else:
                if self._skip is None:
                    count += 1
                else:
                    count = self._skip
                yield (count, cmd, self._app_label, self._app_flags)

    def execute(self, files,  # noqa: E501 pylint: disable=too-many-branches,too-many-statements,too-many-locals
                number=0, label=None, flags="", mimetype=None):
        """Executes the given list of files.

        By default, this executes the first command where all conditions apply,
        but by specifying number=N you can run the 1+Nth command.

        If a label is specified, only rules with this label will be considered.

        If you specify the mimetype, rifle will not try to determine it itself.

        By specifying a flag, you extend the flag that is defined in the rule.
        Uppercase flags negate the respective lowercase flags.
        For example: if the flag in the rule is "pw" and you specify "Pf", then
        the "p" flag is negated and the "f" flag is added, resulting in "wf".
        """
        command = None
        found_at_least_one = None

        # Determine command
        for count, cmd, lbl, flgs in self.list_commands(files, mimetype):
            if label and label == lbl or not label and count == number:
                cmd = self.hook_command_preprocessing(cmd)
                if cmd == ASK_COMMAND:
                    return ASK_COMMAND
                command = self._build_command(files, cmd, flags + flgs)
                flags = self._app_flags
                break
            else:
                found_at_least_one = True
        else:
            if label and label in get_executables():
                cmd = '%s "$@"' % label
                command = self._build_command(files, cmd, flags)

        # Execute command
        if command is None:  # pylint: disable=too-many-nested-blocks
            if found_at_least_one:
                if label:
                    self.hook_logger("Label '%s' is undefined" % label)
                else:
                    self.hook_logger("Method number %d is undefined." % number)
            else:
                self.hook_logger("No action found.")
        else:
            if 'PAGER' not in os.environ:
                os.environ['PAGER'] = DEFAULT_PAGER
            if 'EDITOR' not in os.environ:
                os.environ['EDITOR'] = os.environ.get('VISUAL', DEFAULT_EDITOR)
            command = self.hook_command_postprocessing(command)
            self.hook_before_executing(command, self._mimetype, self._app_flags)
            try:
                if 'r' in flags:
                    prefix = ['sudo', '-E', 'su', 'root', '-mc']
                else:
                    prefix = ['/bin/sh', '-c']

                cmd = prefix + [command]
                if 't' in flags:
                    term = os.environ.get('TERMCMD', os.environ['TERM'])

                    # Handle aliases of xterm and urxvt, rxvt and st and
                    # termite
                    # Match 'xterm', 'xterm-256color'
                    if term in ['xterm', 'xterm-256color']:
                        term = 'xterm'
                    if term in ['xterm-kitty']:
                        term = 'kitty'
                    if term in ['xterm-termite']:
                        term = 'termite'
                    if term in ['st', 'st-256color']:
                        term = 'st'
                    if term in ['urxvt', 'rxvt-unicode',
                                'rxvt-unicode-256color']:
                        term = 'urxvt'
                    if term in ['rxvt', 'rxvt-256color']:
                        if 'rxvt' in get_executables():
                            term = 'rxvt'
                        else:
                            term = 'urxvt'

                    if term not in get_executables():
                        self.hook_logger("Can not determine terminal command, "
                                         "using rifle to determine fallback.  "
                                         "Please set $TERMCMD manually or "
                                         "change fallbacks in rifle.conf.")
                        self._mimetype = 'ranger/x-terminal-emulator'
                        self.execute(
                            files=[command.split(';')[1].split('--')[0].strip()]
                            + files, flags='f',
                            mimetype='ranger/x-terminal-emulator')
                        return None

                    # Choose correct cmdflag accordingly
                    if term in ['xfce4-terminal', 'mate-terminal',
                                'terminator']:
                        cmdflag = '-x'
                    elif term in ['xterm', 'urxvt', 'rxvt', 'lxterminal',
                                  'konsole', 'lilyterm', 'cool-retro-term',
                                  'terminology', 'pantheon-terminal', 'termite',
                                  'st', 'stterm']:
                        cmdflag = '-e'
                    elif term in ['gnome-terminal', 'kitty']:
                        cmdflag = '--'
                    elif term in ['tilda', ]:
                        cmdflag = '-c'
                    else:
                        cmdflag = '-e'

                    os.environ['TERMCMD'] = term

                    # These terms don't work with the '/bin/sh set --' scheme.
                    # A temporary fix.
                    if term in ['tilda', 'pantheon-terminal', 'terminology',
                                'termite']:

                        target = command.split(';')[0].split('--')[1].strip()
                        app = command.split(';')[1].split('--')[0].strip()
                        cmd = [os.environ['TERMCMD'], cmdflag, '%s %s'
                               % (app, target)]
                    elif term in ['guake']:
                        cmd = [os.environ['TERMCMD'], '-n', '${PWD}', cmdflag] + cmd
                    else:
                        cmd = [os.environ['TERMCMD'], cmdflag] + cmd

                    # self.hook_logger('cmd: %s' %cmd)

                if 'f' in flags or 't' in flags:
                    Popen_forked(cmd, env=self.hook_environment(os.environ))
                else:
                    process = Popen(cmd, env=self.hook_environment(os.environ))
                    process.wait()
            finally:
                self.hook_after_executing(command, self._mimetype, self._app_flags)

        return None


def find_conf_path():
    # Find configuration file path
    if 'XDG_CONFIG_HOME' in os.environ and os.environ['XDG_CONFIG_HOME']:
        conf_path = os.environ['XDG_CONFIG_HOME'] + '/ranger/rifle.conf'
    else:
        conf_path = os.path.expanduser('~/.config/ranger/rifle.conf')
    default_conf_path = conf_path
    if not os.path.isfile(conf_path):
        conf_path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                                  '../config/rifle.conf'))
    if not os.path.isfile(conf_path):
        try:
            # if ranger is installed, get the configuration from ranger
            import ranger
        except ImportError:
            pass
        else:
            conf_path = os.path.join(ranger.__path__[0], "config", "rifle.conf")

    if not os.path.isfile(conf_path):
        sys.stderr.write("Could not find a configuration file.\n"
                         "Please create one at %s.\n" % default_conf_path)
        return None

    return conf_path


def main():  # pylint: disable=too-many-locals
    """The main function which is run when you start this program direectly."""

    # Evaluate arguments
    from optparse import OptionParser  # pylint: disable=deprecated-module
    parser = OptionParser(usage="%prog [-fhlpw] [files]", version=__version__)
    parser.add_option('-f', type="string", default="", metavar="FLAGS",
                      help="use additional flags: f=fork, r=root, t=terminal. "
                      "Uppercase flag negates respective lowercase flags.")
    parser.add_option('-l', action="store_true",
                      help="list possible ways to open the files (id:label:flags:command)")
    parser.add_option('-p', type='string', default='0', metavar="KEYWORD",
                      help="pick a method to open the files.  KEYWORD is either the "
                      "number listed by 'rifle -l' or a string that matches a label in "
                      "the configuration file")
    parser.add_option('-w', type='string', default=None, metavar="PROGRAM",
                      help="open the files with PROGRAM")
    parser.add_option('-c', type='string', default=None, metavar="CONFIG_FILE",
                      help="read config from specified file instead of default")
    options, positional = parser.parse_args()
    if not positional:
        parser.print_help()
        raise SystemExit(1)

    if options.c is None:
        conf_path = find_conf_path()
        if not conf_path:
            raise SystemExit(1)
    else:
        try:
            conf_path = os.path.abspath(options.c)
        except OSError as ex:
            sys.stderr.write("Unable to access specified configuration file: {0}\n".format(ex))
            raise SystemExit(1)
        if not os.path.isfile(conf_path):
            sys.stderr.write("Specified configuration file not found: {0}\n".format(conf_path))
            raise SystemExit(1)

    if options.p.isdigit():
        number = int(options.p)
        label = None
    else:
        number = 0
        label = options.p

    if options.w is not None and not options.l:
        process = Popen([options.w] + list(positional))
        process.wait()
    else:
        # Start up rifle
        rifle = Rifle(conf_path)
        rifle.reload_config()
        # print(rifle.list_commands(sys.argv[1:]))
        if options.l:
            for count, cmd, label, flags in rifle.list_commands(positional):
                print("%d:%s:%s:%s" % (count, label or '', flags, cmd))
        else:
            result = rifle.execute(positional, number=number, label=label, flags=options.f)
            if result == ASK_COMMAND:
                # TODO: implement interactive asking for file type?
                print("Unknown file type: %s" %
                      rifle.get_mimetype(positional[0]))


if __name__ == '__main__':
    if 'RANGER_DOCTEST' in os.environ:
        import doctest
        doctest.testmod()
    else:
        main()
