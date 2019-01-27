# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

# TODO: Add an optional "!" to all commands and set a flag if it's there

from __future__ import (absolute_import, division, print_function)

import os
import re

import ranger
from ranger import MACRO_DELIMITER, MACRO_DELIMITER_ESC
from ranger.core.shared import FileManagerAware
from ranger.ext.lazy_property import lazy_property
from ranger.api import LinemodeBase, hook_init, hook_ready, register_linemode  # COMPAT


__all__ = ['Command', 'LinemodeBase', 'hook_init', 'hook_ready', 'register_linemode']  # COMPAT


_SETTINGS_RE = re.compile(r'^\s*([^\s]+?)=(.*)$')
_ALIAS_LINE_RE = re.compile(r'(\s+)')


def _command_init(cls):
    # Escape macros for tab completion
    if cls.resolve_macros:
        tab_old = cls.tab

        def tab(self, tabnum):
            results = tab_old(self, tabnum)
            if results is None:
                return None
            elif isinstance(results, str):
                return results.replace(MACRO_DELIMITER, MACRO_DELIMITER_ESC)
            elif hasattr(results, '__iter__'):
                return (result.replace(MACRO_DELIMITER, MACRO_DELIMITER_ESC) for result in results)
            return None
        setattr(cls, 'tab', tab)

    return cls


class CommandContainer(FileManagerAware):

    def __init__(self):
        self.commands = {}

    def __getitem__(self, key):
        return self.commands[key]

    def alias(self, name, full_command):
        cmd_name = full_command.split()[0]
        cmd_cls = self.get_command(cmd_name)
        if cmd_cls is None:
            self.fm.notify('alias failed: No such command: {0}'.format(cmd_name), bad=True)
        else:
            self.commands[name] = _command_init(command_alias_factory(name, cmd_cls, full_command))

    def load_commands_from_module(self, module):
        for var in vars(module).values():
            try:
                if issubclass(var, Command) and var != Command:
                    self.commands[var.get_name()] = _command_init(var)
            except TypeError:
                pass

    def load_commands_from_object(self, obj, filtr):
        for attribute_name in dir(obj):
            if attribute_name[0] == '_' or attribute_name not in filtr:
                continue
            attribute = getattr(obj, attribute_name)
            if hasattr(attribute, '__call__'):
                self.commands[attribute_name] = _command_init(command_function_factory(attribute))

    def get_command(self, name, abbrev=False):
        if abbrev:
            lst = [cls for cmd, cls in self.commands.items()
                   if cls.allow_abbrev and cmd.startswith(name) or cmd == name]
            if not lst:
                raise KeyError
            if len(lst) == 1:
                return lst[0]
            if self.commands[name] in lst:
                return self.commands[name]
            raise ValueError("Ambiguous command")

        try:
            return self.commands[name]
        except KeyError:
            return None

    def command_generator(self, start):
        return sorted(cmd + ' ' for cmd in self.commands if cmd.startswith(start))


class Command(FileManagerAware):
    """Abstract command class"""
    name = None
    allow_abbrev = True
    resolve_macros = True
    escape_macros_for_shell = False
    quantifier = None
    _shifted = 0
    _setting_line = None

    def __init__(self, line, quantifier=None):
        self.init_line(line)
        self.quantifier = quantifier
        self.quickly_executed = False

    def init_line(self, line):
        self.line = line
        self.args = line.split()
        try:
            self.firstpart = line[:line.rindex(' ') + 1]
        except ValueError:
            self.firstpart = ''

    @classmethod
    def get_name(cls):
        classdict = cls.__mro__[0].__dict__
        if 'name' in classdict and classdict['name']:
            return cls.name
        return cls.__name__

    def execute(self):
        """Override this"""

    def tab(self, tabnum):
        """Override this"""

    def quick(self):
        """Override this"""

    def cancel(self):
        """Override this"""

    # Easy ways to get information
    def arg(self, n):
        """Returns the nth space separated word"""
        try:
            return self.args[n]
        except IndexError:
            return ""

    def rest(self, n):
        """Returns everything from and after arg(n)"""
        got_space = True
        word_count = 0
        for i, char in enumerate(self.line):
            if char.isspace():
                if not got_space:
                    got_space = True
                    word_count += 1
            elif got_space:
                got_space = False
                if word_count == n + self._shifted:
                    return self.line[i:]
        return ""

    def start(self, n):
        """Returns everything until (inclusively) arg(n)"""
        return ' '.join(self.args[:n]) + " "  # XXX

    def shift(self):
        del self.args[0]
        self._setting_line = None
        self._shifted += 1

    def parse_setting_line(self):
        """
        Parses the command line argument that is passed to the `:set` command.
        Returns [option, value, name_complete].

        Can parse incomplete lines too, and `name_complete` is a boolean
        indicating whether the option name looks like it's completed or
        unfinished.  This is useful for generating tab completions.

        >>> Command("set foo=bar").parse_setting_line()
        ['foo', 'bar', True]
        >>> Command("set foo").parse_setting_line()
        ['foo', '', False]
        >>> Command("set foo=").parse_setting_line()
        ['foo', '', True]
        >>> Command("set foo ").parse_setting_line()
        ['foo', '', True]
        >>> Command("set myoption myvalue").parse_setting_line()
        ['myoption', 'myvalue', True]
        >>> Command("set").parse_setting_line()
        ['', '', False]
        """
        if self._setting_line is not None:
            return self._setting_line
        match = _SETTINGS_RE.match(self.rest(1))
        if match:
            self.firstpart += match.group(1) + '='
            result = [match.group(1), match.group(2), True]
        else:
            result = [self.arg(1), self.rest(2), ' ' in self.rest(1)]
        self._setting_line = result
        return result

    def parse_setting_line_v2(self):
        """
        Parses the command line argument that is passed to the `:set` command.
        Returns [option, value, name_complete, toggle].

        >>> Command("set foo=bar").parse_setting_line_v2()
        ['foo', 'bar', True, False]
        >>> Command("set foo!").parse_setting_line_v2()
        ['foo', '', True, True]
        """
        option, value, name_complete = self.parse_setting_line()
        if len(option) >= 2 and option[-1] == '!':
            toggle = True
            option = option[:-1]
            name_complete = True
        else:
            toggle = False
        return [option, value, name_complete, toggle]

    def parse_flags(self):
        """Finds and returns flags in the command

        >>> Command("").parse_flags()
        ('', '')
        >>> Command("foo").parse_flags()
        ('', '')
        >>> Command("shell test").parse_flags()
        ('', 'test')
        >>> Command("shell -t ls -l").parse_flags()
        ('t', 'ls -l')
        >>> Command("shell -f -- -q test").parse_flags()
        ('f', '-q test')
        >>> Command("shell -foo -bar rest of the command").parse_flags()
        ('foobar', 'rest of the command')
        """
        flags = ""
        args = self.line.split()
        rest = ""
        if args:
            rest = self.line[len(args[0]):].lstrip()
            for arg in args[1:]:
                if arg == "--":
                    rest = rest[2:].lstrip()
                    break
                elif len(arg) > 1 and arg[0] == "-":
                    rest = rest[len(arg):].lstrip()
                    flags += arg[1:]
                else:
                    break
        return flags, rest

    @lazy_property
    def log(self):
        import logging
        return logging.getLogger('ranger.commands.' + self.__class__.__name__)

    # COMPAT: this is still used in old commands.py configs
    def _tab_only_directories(self):
        from os.path import dirname, basename, expanduser, join

        cwd = self.fm.thisdir.path

        rel_dest = self.rest(1)

        # expand the tilde into the user directory
        if rel_dest.startswith('~'):
            rel_dest = expanduser(rel_dest)

        # define some shortcuts
        abs_dest = join(cwd, rel_dest)
        abs_dirname = dirname(abs_dest)
        rel_basename = basename(rel_dest)
        rel_dirname = dirname(rel_dest)

        try:
            # are we at the end of a directory?
            if rel_dest.endswith('/') or rel_dest == '':
                _, dirnames, _ = next(os.walk(abs_dest))

            # are we in the middle of the filename?
            else:
                _, dirnames, _ = next(os.walk(abs_dirname))
                dirnames = [dn for dn in dirnames
                            if dn.startswith(rel_basename)]
        except (OSError, StopIteration):
            # os.walk found nothing
            pass
        else:
            dirnames.sort()

            # no results, return None
            if not dirnames:
                return None

            # one result. since it must be a directory, append a slash.
            if len(dirnames) == 1:
                return self.start(1) + join(rel_dirname, dirnames[0]) + '/'

            # more than one result. append no slash, so the user can
            # manually type in the slash to advance into that directory
            return (self.start(1) + join(rel_dirname, dirname)
                    for dirname in dirnames)

    def _tab_directory_content(self):  # pylint: disable=too-many-locals
        from os.path import dirname, basename, expanduser, join

        cwd = self.fm.thisdir.path

        rel_dest = self.rest(1)

        # expand the tilde into the user directory
        if rel_dest.startswith('~'):
            rel_dest = expanduser(rel_dest)

        # define some shortcuts
        abs_dest = join(cwd, rel_dest)
        abs_dirname = dirname(abs_dest)
        rel_basename = basename(rel_dest)
        rel_dirname = dirname(rel_dest)

        try:
            directory = self.fm.get_directory(abs_dest)

            # are we at the end of a directory?
            if rel_dest.endswith('/') or rel_dest == '':
                if directory.content_loaded:
                    # Take the order from the directory object
                    names = [f.basename for f in directory.files]
                    if self.fm.thisfile.basename in names:
                        i = names.index(self.fm.thisfile.basename)
                        names = names[i:] + names[:i]
                else:
                    # Fall back to old method with "os.walk"
                    _, dirnames, filenames = next(os.walk(abs_dest))
                    names = sorted(dirnames + filenames)

            # are we in the middle of the filename?
            else:
                if directory.content_loaded:
                    # Take the order from the directory object
                    names = [f.basename for f in directory.files
                             if f.basename.startswith(rel_basename)]
                    if self.fm.thisfile.basename in names:
                        i = names.index(self.fm.thisfile.basename)
                        names = names[i:] + names[:i]
                else:
                    # Fall back to old method with "os.walk"
                    _, dirnames, filenames = next(os.walk(abs_dirname))
                    names = sorted([name for name in (dirnames + filenames)
                                    if name.startswith(rel_basename)])
        except (OSError, StopIteration):
            # os.walk found nothing
            pass
        else:
            # no results, return None
            if not names:
                return None

            # one result. append a slash if it's a directory
            if len(names) == 1:
                path = join(rel_dirname, names[0])
                slash = '/' if os.path.isdir(path) else ''
                return self.start(1) + path + slash

            # more than one result. append no slash, so the user can
            # manually type in the slash to advance into that directory
            return (self.start(1) + join(rel_dirname, name) for name in names)

    def _tab_through_executables(self):
        from ranger.ext.get_executables import get_executables
        programs = [program for program in get_executables() if
                    program.startswith(self.rest(1))]
        if not programs:
            return None
        if len(programs) == 1:
            return self.start(1) + programs[0]
        programs.sort()
        return (self.start(1) + program for program in programs)


def command_alias_factory(name, cls, full_command):
    class CommandAlias(cls):   # pylint: disable=too-few-public-methods
        def __init__(self, line, *args, **kwargs):
            super(CommandAlias, self).__init__(
                (full_command + ''.join(_ALIAS_LINE_RE.split(line)[1:])), *args, **kwargs)

    CommandAlias.__name__ = name
    return CommandAlias


def command_function_factory(func):
    class CommandFunction(Command):
        __doc__ = func.__doc__

        def execute(self):  # pylint: disable=too-many-branches
            if not func:
                return None
            if len(self.args) == 1:
                try:
                    return func(**{'narg': self.quantifier})
                except TypeError:
                    return func()

            args, kwargs = list(), dict()
            for arg in self.args[1:]:
                equal_sign = arg.find("=")
                value = arg if equal_sign == -1 else arg[equal_sign + 1:]
                try:
                    value = int(value)
                except ValueError:
                    if value in ('True', 'False'):
                        value = (value == 'True')
                    else:
                        try:
                            value = float(value)
                        except ValueError:
                            pass

                if equal_sign == -1:
                    args.append(value)
                else:
                    kwargs[arg[:equal_sign]] = value

            if self.quantifier is not None:
                kwargs['narg'] = self.quantifier

            try:
                if self.quantifier is None:
                    return func(*args, **kwargs)
                else:
                    try:
                        return func(*args, **kwargs)
                    except TypeError:
                        del kwargs['narg']
                        return func(*args, **kwargs)
            except TypeError:
                if ranger.args.debug:
                    raise
                self.fm.notify("Bad arguments for %s: %s, %s" % (func.__name__, args, kwargs),
                               bad=True)

    CommandFunction.__name__ = func.__name__
    return CommandFunction


if __name__ == '__main__':
    import doctest
    import sys
    sys.exit(doctest.testmod()[0])
