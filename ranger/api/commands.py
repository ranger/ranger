# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

# TODO: Add an optional "!" to all commands and set a flag if it's there

import os
import ranger
import re
import inspect
from collections import deque
from ranger.api import *
from ranger.core.shared import FileManagerAware
from ranger.ext.lazy_property import lazy_property

_SETTINGS_RE = re.compile(r'^\s*([^\s]+?)=(.*)$')


class CommandContainer(object):
    def __init__(self):
        self.commands = {}

    def __getitem__(self, key):
        return self.commands[key]

    def alias(self, name, full_command):
        try:
            cmd = type(name, (AliasCommand, ), dict())
            cmd._based_function = name
            cmd._function_name = name
            cmd._object_name = name
            cmd._line = full_command
            self.commands[name] = cmd

        except Exception:
            pass

    def load_commands_from_module(self, module):
        for var in vars(module).values():
            try:
                if issubclass(var, Command) and var != Command \
                        and var != FunctionCommand:
                    self.commands[var.get_name()] = var
            except TypeError:
                pass

    def load_commands_from_object(self, obj, filtr):
        for attribute_name in dir(obj):
            if attribute_name[0] == '_' or attribute_name not in filtr:
                continue
            attribute = getattr(obj, attribute_name)
            if hasattr(attribute, '__call__'):
                cmd = type(attribute_name, (FunctionCommand, ), dict(__doc__=attribute.__doc__))
                cmd._based_function = attribute
                cmd._function_name = attribute.__name__
                cmd._object_name = obj.__class__.__name__
                self.commands[attribute_name] = cmd

    def get_command(self, name, abbrev=True):
        if abbrev:
            lst = [cls for cmd, cls in self.commands.items()
                    if cls.allow_abbrev and cmd.startswith(name)
                    or cmd == name]
            if len(lst) == 0:
                raise KeyError
            if len(lst) == 1:
                return lst[0]
            if self.commands[name] in lst:
                return self.commands[name]
            raise ValueError("Ambiguous command")
        else:
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
        self.line = line
        self.args = line.split()
        self.quantifier = quantifier
        self.quickly_executed = False
        try:
            self.firstpart = line[:line.rindex(' ') + 1]
        except ValueError:
            self.firstpart = ''

    @classmethod
    def get_name(self):
        classdict = self.__mro__[0].__dict__
        if 'name' in classdict and classdict['name']:
            return self.name
        else:
            return self.__name__

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
        for i in range(len(self.line)):
            if self.line[i] == " ":
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

    def tabinsert(self, word):
        return ''.join([self._tabinsert_left, word, self._tabinsert_right])

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
        if len(args) > 0:
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

    # XXX: Lazy properties? Not so smart? self.line can change after all!
    @lazy_property
    def _tabinsert_left(self):
        try:
            return self.line[:self.line[0:self.pos].rindex(' ') + 1]
        except ValueError:
            return ''

    @lazy_property
    def _tabinsert_right(self):
        return self.line[self.pos:]

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
            if len(dirnames) == 0:
                return

            # one result. since it must be a directory, append a slash.
            if len(dirnames) == 1:
                return self.start(1) + join(rel_dirname, dirnames[0]) + '/'

            # more than one result. append no slash, so the user can
            # manually type in the slash to advance into that directory
            return (self.start(1) + join(rel_dirname, dirname)
                    for dirname in dirnames)

    def _tab_directory_content(self):
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
                    names = dirnames + filenames
                    names.sort()

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
                    names = [name for name in (dirnames + filenames)
                            if name.startswith(rel_basename)]
                    names.sort()
        except (OSError, StopIteration):
            # os.walk found nothing
            pass
        else:
            # no results, return None
            if len(names) == 0:
                return

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
            return
        if len(programs) == 1:
            return self.start(1) + programs[0]
        programs.sort()
        return (self.start(1) + program for program in programs)


class FunctionCommand(Command):
    _based_function = None
    _object_name = ""
    _function_name = "unknown"

    def execute(self):
        if not self._based_function:
            return
        if len(self.args) == 1:
            try:
                return self._based_function(**{'narg': self.quantifier})
            except TypeError:
                return self._based_function()

        args, keywords = list(), dict()
        for arg in self.args[1:]:
            equal_sign = arg.find("=")
            value = arg if (equal_sign is -1) else arg[equal_sign + 1:]
            try:
                value = int(value)
            except Exception:
                if value in ('True', 'False'):
                    value = (value == 'True')
                else:
                    try:
                        value = float(value)
                    except Exception:
                        pass

            if equal_sign == -1:
                args.append(value)
            else:
                keywords[arg[:equal_sign]] = value

        if self.quantifier is not None:
            keywords['narg'] = self.quantifier

        try:
            if self.quantifier is None:
                return self._based_function(*args, **keywords)
            else:
                try:
                    return self._based_function(*args, **keywords)
                except TypeError:
                    del keywords['narg']
                    return self._based_function(*args, **keywords)
        except TypeError:
            if ranger.arg.debug:
                raise
            else:
                self.fm.notify("Bad arguments for %s.%s: %s, %s" %
                        (self._object_name, self._function_name,
                            repr(args), repr(keywords)), bad=True)


class AliasCommand(Command):
    _based_function = None
    _object_name = ""
    _function_name = "unknown"
    _line = ""

    def execute(self):
        return self._make_cmd().execute()

    def quick(self):
        return self._make_cmd().quick()

    def tab(self, tabnum):
        cmd = self._make_cmd()
        args = inspect.signature(cmd.tab).parameters if self.fm.py3 else \
            inspect.getargspec(cmd.tab).args
        return cmd.tab(tabnum) if 'tabnum' in args else cmd.tab()

    def cancel(self):
        return self._make_cmd().cancel()

    def _make_cmd(self):
        cmd_class = self.fm.commands.get_command(self._line.split()[0])
        cmd = cmd_class(self._line + ' ' + self.rest(1))
        cmd.quickly_executed = self.quickly_executed
        cmd.quantifier = self.quantifier
        cmd.escape_macros_for_shell = self.escape_macros_for_shell
        cmd.resolve_macros = self.resolve_macros
        cmd.allow_abbrev = self.allow_abbrev
        return cmd


if __name__ == '__main__':
    import doctest
    doctest.testmod()
