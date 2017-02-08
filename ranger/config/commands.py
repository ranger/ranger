# -*- coding: utf-8 -*-
# This file is part of ranger, the console file manager.
# This configuration file is licensed under the same terms as ranger.
# ===================================================================
#
# NOTE: If you copied this file to ~/.config/ranger/commands_full.py,
# then it will NOT be loaded by ranger, and only serve as a reference.
#
# ===================================================================
# This file contains ranger's commands.
# It's all in python; lines beginning with # are comments.
#
# Note that additional commands are automatically generated from the methods
# of the class ranger.core.actions.Actions.
#
# You can customize commands in the file ~/.config/ranger/commands.py.
# It has the same syntax as this file.  In fact, you can just copy this
# file there with `ranger --copy-config=commands' and make your modifications.
# But make sure you update your configs when you update ranger.
#
# ===================================================================
# Every class defined here which is a subclass of `Command' will be used as a
# command in ranger.  Several methods are defined to interface with ranger:
#   execute():   called when the command is executed.
#   cancel():    called when closing the console.
#   tab(tabnum): called when <TAB> is pressed.
#   quick():     called after each keypress.
#
# tab() argument tabnum is 1 for <TAB> and -1 for <S-TAB> by default
#
# The return values for tab() can be either:
#   None: There is no tab completion
#   A string: Change the console to this string
#   A list/tuple/generator: cycle through every item in it
#
# The return value for quick() can be:
#   False: Nothing happens
#   True: Execute the command afterwards
#
# The return value for execute() and cancel() doesn't matter.
#
# ===================================================================
# Commands have certain attributes and methods that facilitate parsing of
# the arguments:
#
# self.line: The whole line that was written in the console.
# self.args: A list of all (space-separated) arguments to the command.
# self.quantifier: If this command was mapped to the key "X" and
#      the user pressed 6X, self.quantifier will be 6.
# self.arg(n): The n-th argument, or an empty string if it doesn't exist.
# self.rest(n): The n-th argument plus everything that followed.  For example,
#      if the command was "search foo bar a b c", rest(2) will be "bar a b c"
# self.start(n): Anything before the n-th argument.  For example, if the
#      command was "search foo bar a b c", start(2) will be "search foo"
#
# ===================================================================
# And this is a little reference for common ranger functions and objects:
#
# self.fm: A reference to the "fm" object which contains most information
#      about ranger.
# self.fm.notify(string): Print the given string on the screen.
# self.fm.notify(string, bad=True): Print the given string in RED.
# self.fm.reload_cwd(): Reload the current working directory.
# self.fm.thisdir: The current working directory. (A File object.)
# self.fm.thisfile: The current file. (A File object too.)
# self.fm.thistab.get_selection(): A list of all selected files.
# self.fm.execute_console(string): Execute the string as a ranger command.
# self.fm.open_console(string): Open the console with the given string
#      already typed in for you.
# self.fm.move(direction): Moves the cursor in the given direction, which
#      can be something like down=3, up=5, right=1, left=1, to=6, ...
#
# File objects (for example self.fm.thisfile) have these useful attributes and
# methods:
#
# tfile.path: The path to the file.
# tfile.basename: The base name only.
# tfile.load_content(): Force a loading of the directories content (which
#      obviously works with directories only)
# tfile.is_directory: True/False depending on whether it's a directory.
#
# For advanced commands it is unavoidable to dive a bit into the source code
# of ranger.
# ===================================================================

from __future__ import (absolute_import, division, print_function)

from collections import deque
import os
import re

from ranger.api.commands import Command


class alias(Command):
    """:alias <newcommand> <oldcommand>

    Copies the oldcommand as newcommand.
    """

    context = 'browser'
    resolve_macros = False

    def execute(self):
        if not self.arg(1) or not self.arg(2):
            self.fm.notify('Syntax: alias <newcommand> <oldcommand>', bad=True)
            return

        self.fm.commands.alias(self.arg(1), self.rest(2))


class echo(Command):
    """:echo <text>

    Display the text in the statusbar.
    """

    def execute(self):
        self.fm.notify(self.rest(1))


class cd(Command):
    """:cd [-r] <dirname>

    The cd command changes the directory.
    The command 'cd -' is equivalent to typing ``.
    Using the option "-r" will get you to the real path.
    """

    def execute(self):
        if self.arg(1) == '-r':
            self.shift()
            destination = os.path.realpath(self.rest(1))
            if os.path.isfile(destination):
                self.fm.select_file(destination)
                return
        else:
            destination = self.rest(1)

        if not destination:
            destination = '~'

        if destination == '-':
            self.fm.enter_bookmark('`')
        else:
            self.fm.cd(destination)

    def tab(self, tabnum):  # pylint: disable=too-many-locals
        from os.path import dirname, basename, expanduser, join

        cwd = self.fm.thisdir.path
        rel_dest = self.rest(1)

        bookmarks = [v.path for v in self.fm.bookmarks.dct.values()
                     if rel_dest in v.path]

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
            if self.fm.settings.cd_bookmarks:
                dirnames = bookmarks + dirnames

            # no results, return None
            if not dirnames:
                return

            # one result. since it must be a directory, append a slash.
            if len(dirnames) == 1:
                return self.start(1) + join(rel_dirname, dirnames[0]) + '/'

            # more than one result. append no slash, so the user can
            # manually type in the slash to advance into that directory
            return (self.start(1) + join(rel_dirname, dirname) for dirname in dirnames)


class chain(Command):
    """:chain <command1>; <command2>; ...

    Calls multiple commands at once, separated by semicolons.
    """

    def execute(self):
        for command in [s.strip() for s in self.rest(1).split(";")]:
            self.fm.execute_console(command)


class shell(Command):
    escape_macros_for_shell = True

    def execute(self):
        if self.arg(1) and self.arg(1)[0] == '-':
            flags = self.arg(1)[1:]
            command = self.rest(2)
        else:
            flags = ''
            command = self.rest(1)

        if command:
            self.fm.execute_command(command, flags=flags)

    def tab(self, tabnum):
        from ranger.ext.get_executables import get_executables
        if self.arg(1) and self.arg(1)[0] == '-':
            command = self.rest(2)
        else:
            command = self.rest(1)
        start = self.line[0:len(self.line) - len(command)]

        try:
            position_of_last_space = command.rindex(" ")
        except ValueError:
            return (start + program + ' ' for program
                    in get_executables() if program.startswith(command))
        if position_of_last_space == len(command) - 1:
            selection = self.fm.thistab.get_selection()
            if len(selection) == 1:
                return self.line + selection[0].shell_escaped_basename + ' '
            return self.line + '%s '

        before_word, start_of_word = self.line.rsplit(' ', 1)
        return (before_word + ' ' + file.shell_escaped_basename
                for file in self.fm.thisdir.files or []
                if file.shell_escaped_basename.startswith(start_of_word))


class open_with(Command):

    def execute(self):
        app, flags, mode = self._get_app_flags_mode(self.rest(1))
        self.fm.execute_file(
            files=[f for f in self.fm.thistab.get_selection()],
            app=app,
            flags=flags,
            mode=mode)

    def tab(self, tabnum):
        return self._tab_through_executables()

    def _get_app_flags_mode(self, string):  # pylint: disable=too-many-branches,too-many-statements
        """Extracts the application, flags and mode from a string.

        examples:
        "mplayer f 1" => ("mplayer", "f", 1)
        "atool 4" => ("atool", "", 4)
        "p" => ("", "p", 0)
        "" => None
        """

        app = ''
        flags = ''
        mode = 0
        split = string.split()

        if len(split) == 1:
            part = split[0]
            if self._is_app(part):
                app = part
            elif self._is_flags(part):
                flags = part
            elif self._is_mode(part):
                mode = part

        elif len(split) == 2:
            part0 = split[0]
            part1 = split[1]

            if self._is_app(part0):
                app = part0
                if self._is_flags(part1):
                    flags = part1
                elif self._is_mode(part1):
                    mode = part1
            elif self._is_flags(part0):
                flags = part0
                if self._is_mode(part1):
                    mode = part1
            elif self._is_mode(part0):
                mode = part0
                if self._is_flags(part1):
                    flags = part1

        elif len(split) >= 3:
            part0 = split[0]
            part1 = split[1]
            part2 = split[2]

            if self._is_app(part0):
                app = part0
                if self._is_flags(part1):
                    flags = part1
                    if self._is_mode(part2):
                        mode = part2
                elif self._is_mode(part1):
                    mode = part1
                    if self._is_flags(part2):
                        flags = part2
            elif self._is_flags(part0):
                flags = part0
                if self._is_mode(part1):
                    mode = part1
            elif self._is_mode(part0):
                mode = part0
                if self._is_flags(part1):
                    flags = part1

        return app, flags, int(mode)

    def _is_app(self, arg):
        return not self._is_flags(arg) and not arg.isdigit()

    @staticmethod
    def _is_flags(arg):
        from ranger.core.runner import ALLOWED_FLAGS
        return all(x in ALLOWED_FLAGS for x in arg)

    @staticmethod
    def _is_mode(arg):
        return all(x in '0123456789' for x in arg)


class set_(Command):
    """:set <option name>=<python expression>

    Gives an option a new value.

    Use `:set <option>!` to toggle or cycle it, e.g. `:set flush_input!`
    """
    name = 'set'  # don't override the builtin set class

    def execute(self):
        name = self.arg(1)
        name, value, _, toggle = self.parse_setting_line_v2()
        if toggle:
            self.fm.toggle_option(name)
        else:
            self.fm.set_option_from_string(name, value)

    def tab(self, tabnum):  # pylint: disable=too-many-return-statements
        from ranger.gui.colorscheme import get_all_colorschemes
        name, value, name_done = self.parse_setting_line()
        settings = self.fm.settings
        if not name:
            return sorted(self.firstpart + setting for setting in settings)
        if not value and not name_done:
            return sorted(self.firstpart + setting for setting in settings
                          if setting.startswith(name))
        if not value:
            # Cycle through colorschemes when name, but no value is specified
            if name == "colorscheme":
                return sorted(self.firstpart + colorscheme for colorscheme
                              in get_all_colorschemes(self.fm))
            return self.firstpart + str(settings[name])
        if bool in settings.types_of(name):
            if 'true'.startswith(value.lower()):
                return self.firstpart + 'True'
            if 'false'.startswith(value.lower()):
                return self.firstpart + 'False'
        # Tab complete colorscheme values if incomplete value is present
        if name == "colorscheme":
            return sorted(self.firstpart + colorscheme for colorscheme
                          in get_all_colorschemes(self.fm) if colorscheme.startswith(value))


class setlocal(set_):
    """:setlocal path=<regular expression> <option name>=<python expression>

    Gives an option a new value.
    """
    PATH_RE_DQUOTED = re.compile(r'^setlocal\s+path="(.*?)"')
    PATH_RE_SQUOTED = re.compile(r"^setlocal\s+path='(.*?)'")
    PATH_RE_UNQUOTED = re.compile(r'^path=(.*?)$')

    def _re_shift(self, match):
        if not match:
            return None
        path = os.path.expanduser(match.group(1))
        for _ in range(len(path.split())):
            self.shift()
        return path

    def execute(self):
        path = self._re_shift(self.PATH_RE_DQUOTED.match(self.line))
        if path is None:
            path = self._re_shift(self.PATH_RE_SQUOTED.match(self.line))
        if path is None:
            path = self._re_shift(self.PATH_RE_UNQUOTED.match(self.arg(1)))
        if path is None and self.fm.thisdir:
            path = self.fm.thisdir.path
        if not path:
            return

        name, value, _ = self.parse_setting_line()
        self.fm.set_option_from_string(name, value, localpath=path)


class setintag(set_):
    """:setintag <tag or tags> <option name>=<option value>

    Sets an option for directories that are tagged with a specific tag.
    """

    def execute(self):
        tags = self.arg(1)
        self.shift()
        name, value, _ = self.parse_setting_line()
        self.fm.set_option_from_string(name, value, tags=tags)


class default_linemode(Command):

    def execute(self):
        from ranger.container.fsobject import FileSystemObject

        if len(self.args) < 2:
            self.fm.notify(
                "Usage: default_linemode [path=<regexp> | tag=<tag(s)>] <linemode>", bad=True)

        # Extract options like "path=..." or "tag=..." from the command line
        arg1 = self.arg(1)
        method = "always"
        argument = None
        if arg1.startswith("path="):
            method = "path"
            argument = re.compile(arg1[5:])
            self.shift()
        elif arg1.startswith("tag="):
            method = "tag"
            argument = arg1[4:]
            self.shift()

        # Extract and validate the line mode from the command line
        lmode = self.rest(1)
        if lmode not in FileSystemObject.linemode_dict:
            self.fm.notify(
                "Invalid linemode: %s; should be %s" % (
                    lmode, "/".join(FileSystemObject.linemode_dict)),
                bad=True,
            )

        # Add the prepared entry to the fm.default_linemodes
        entry = [method, argument, lmode]
        self.fm.default_linemodes.appendleft(entry)

        # Redraw the columns
        if self.fm.ui.browser:
            for col in self.fm.ui.browser.columns:
                col.need_redraw = True

    def tab(self, tabnum):
        return (self.arg(0) + " " + lmode
                for lmode in self.fm.thisfile.linemode_dict.keys()
                if lmode.startswith(self.arg(1)))


class quit(Command):  # pylint: disable=redefined-builtin
    """:quit

    Closes the current tab, if there's only one tab.
    Otherwise quits if there are no tasks in progress.
    """
    def _exit_no_work(self):
        if self.fm.loader.has_work():
            self.fm.notify('Not quitting: Tasks in progress: Use `quit!` to force quit')
        else:
            self.fm.exit()

    def execute(self):
        if len(self.fm.tabs) >= 2:
            self.fm.tab_close()
        else:
            self._exit_no_work()


class quit_bang(Command):
    """:quit!

    Closes the current tab, if there's only one tab.
    Otherwise force quits immediately.
    """
    name = 'quit!'
    allow_abbrev = False

    def execute(self):
        if len(self.fm.tabs) >= 2:
            self.fm.tab_close()
        else:
            self.fm.exit()


class quitall(Command):
    """:quitall

    Quits if there are no tasks in progress.
    """
    def _exit_no_work(self):
        if self.fm.loader.has_work():
            self.fm.notify('Not quitting: Tasks in progress: Use `quitall!` to force quit')
        else:
            self.fm.exit()

    def execute(self):
        self._exit_no_work()


class quitall_bang(Command):
    """:quitall!

    Force quits immediately.
    """
    name = 'quitall!'
    allow_abbrev = False

    def execute(self):
        self.fm.exit()


class terminal(Command):
    """:terminal

    Spawns an "x-terminal-emulator" starting in the current directory.
    """

    def execute(self):
        from ranger.ext.get_executables import get_term
        self.fm.run(get_term(), flags='f')


class delete(Command):
    """:delete

    Tries to delete the selection or the files passed in arguments (if any).
    The arguments use a shell-like escaping.

    "Selection" is defined as all the "marked files" (by default, you
    can mark files with space or v). If there are no marked files,
    use the "current file" (where the cursor is)

    When attempting to delete non-empty directories or multiple
    marked files, it will require a confirmation.
    """

    allow_abbrev = False
    escape_macros_for_shell = True

    def execute(self):
        import shlex
        from functools import partial

        def is_directory_with_files(path):
            return os.path.isdir(path) and not os.path.islink(path) and len(os.listdir(path)) > 0

        if self.rest(1):
            files = shlex.split(self.rest(1))
            many_files = (len(files) > 1 or is_directory_with_files(files[0]))
        else:
            cwd = self.fm.thisdir
            tfile = self.fm.thisfile
            if not cwd or not tfile:
                self.fm.notify("Error: no file selected for deletion!", bad=True)
                return

            # relative_path used for a user-friendly output in the confirmation.
            files = [f.relative_path for f in self.fm.thistab.get_selection()]
            many_files = (cwd.marked_items or is_directory_with_files(tfile.path))

        confirm = self.fm.settings.confirm_on_delete
        if confirm != 'never' and (confirm != 'multiple' or many_files):
            self.fm.ui.console.ask(
                "Confirm deletion of: %s (y/N)" % ', '.join(files),
                partial(self._question_callback, files),
                ('n', 'N', 'y', 'Y'),
            )
        else:
            # no need for a confirmation, just delete
            self.fm.delete(files)

    def tab(self, tabnum):
        return self._tab_directory_content()

    def _question_callback(self, files, answer):
        if answer == 'y' or answer == 'Y':
            self.fm.delete(files)


class jump_non(Command):
    """:jump_non [-FLAGS...]

    Jumps to first non-directory if highlighted file is a directory and vice versa.

    Flags:
     -r    Jump in reverse order
     -w    Wrap around if reaching end of filelist
    """
    def __init__(self, *args, **kwargs):
        super(jump_non, self).__init__(*args, **kwargs)

        flags, _ = self.parse_flags()
        self._flag_reverse = 'r' in flags
        self._flag_wrap = 'w' in flags

    @staticmethod
    def _non(fobj, is_directory):
        return fobj.is_directory if not is_directory else not fobj.is_directory

    def execute(self):
        tfile = self.fm.thisfile
        passed = False
        found_before = None
        found_after = None
        for fobj in self.fm.thisdir.files[::-1] if self._flag_reverse else self.fm.thisdir.files:
            if fobj.path == tfile.path:
                passed = True
                continue

            if passed:
                if self._non(fobj, tfile.is_directory):
                    found_after = fobj.path
                    break
            elif not found_before and self._non(fobj, tfile.is_directory):
                found_before = fobj.path

        if found_after:
            self.fm.select_file(found_after)
        elif self._flag_wrap and found_before:
            self.fm.select_file(found_before)


class mark_tag(Command):
    """:mark_tag [<tags>]

    Mark all tags that are tagged with either of the given tags.
    When leaving out the tag argument, all tagged files are marked.
    """
    do_mark = True

    def execute(self):
        cwd = self.fm.thisdir
        tags = self.rest(1).replace(" ", "")
        if not self.fm.tags or not cwd.files:
            return
        for fileobj in cwd.files:
            try:
                tag = self.fm.tags.tags[fileobj.realpath]
            except KeyError:
                continue
            if not tags or tag in tags:
                cwd.mark_item(fileobj, val=self.do_mark)
        self.fm.ui.status.need_redraw = True
        self.fm.ui.need_redraw = True


class console(Command):
    """:console <command>

    Open the console with the given command.
    """

    def execute(self):
        position = None
        if self.arg(1)[0:2] == '-p':
            try:
                position = int(self.arg(1)[2:])
            except ValueError:
                pass
            else:
                self.shift()
        self.fm.open_console(self.rest(1), position=position)


class load_copy_buffer(Command):
    """:load_copy_buffer

    Load the copy buffer from datadir/copy_buffer
    """
    copy_buffer_filename = 'copy_buffer'

    def execute(self):
        from ranger.container.file import File
        from os.path import exists
        fname = self.fm.datapath(self.copy_buffer_filename)
        try:
            fobj = open(fname, 'r')
        except OSError:
            return self.fm.notify(
                "Cannot open %s" % (fname or self.copy_buffer_filename), bad=True)
        self.fm.copy_buffer = set(File(g)
                                  for g in fobj.read().split("\n") if exists(g))
        fobj.close()
        self.fm.ui.redraw_main_column()


class save_copy_buffer(Command):
    """:save_copy_buffer

    Save the copy buffer to datadir/copy_buffer
    """
    copy_buffer_filename = 'copy_buffer'

    def execute(self):
        fname = None
        fname = self.fm.datapath(self.copy_buffer_filename)
        try:
            fobj = open(fname, 'w')
        except OSError:
            return self.fm.notify("Cannot open %s" %
                                  (fname or self.copy_buffer_filename), bad=True)
        fobj.write("\n".join(fobj.path for fobj in self.fm.copy_buffer))
        fobj.close()


class unmark_tag(mark_tag):
    """:unmark_tag [<tags>]

    Unmark all tags that are tagged with either of the given tags.
    When leaving out the tag argument, all tagged files are unmarked.
    """
    do_mark = False


class mkdir(Command):
    """:mkdir <dirname>

    Creates a directory with the name <dirname>.
    """

    def execute(self):
        from os.path import join, expanduser, lexists
        from os import makedirs

        dirname = join(self.fm.thisdir.path, expanduser(self.rest(1)))
        if not lexists(dirname):
            makedirs(dirname)
        else:
            self.fm.notify("file/directory exists!", bad=True)

    def tab(self, tabnum):
        return self._tab_directory_content()


class touch(Command):
    """:touch <fname>

    Creates a file with the name <fname>.
    """

    def execute(self):
        from os.path import join, expanduser, lexists

        fname = join(self.fm.thisdir.path, expanduser(self.rest(1)))
        if not lexists(fname):
            open(fname, 'a').close()
        else:
            self.fm.notify("file/directory exists!", bad=True)

    def tab(self, tabnum):
        return self._tab_directory_content()


class edit(Command):
    """:edit <filename>

    Opens the specified file in vim
    """

    def execute(self):
        if not self.arg(1):
            self.fm.edit_file(self.fm.thisfile.path)
        else:
            self.fm.edit_file(self.rest(1))

    def tab(self, tabnum):
        return self._tab_directory_content()


class eval_(Command):
    """:eval [-q] <python code>

    Evaluates the python code.
    `fm' is a reference to the FM instance.
    To display text, use the function `p'.

    Examples:
    :eval fm
    :eval len(fm.directories)
    :eval p("Hello World!")
    """
    name = 'eval'
    resolve_macros = False

    def execute(self):
        if self.arg(1) == '-q':
            code = self.rest(2)
            quiet = True
        else:
            code = self.rest(1)
            quiet = False
        global cmd, fm, p, quantifier  # pylint: disable=invalid-name,global-variable-undefined
        fm = self.fm
        cmd = self.fm.execute_console
        p = fm.notify
        quantifier = self.quantifier
        try:
            try:
                result = eval(code)  # pylint: disable=eval-used
            except SyntaxError:
                exec(code)  # pylint: disable=exec-used
            else:
                if result and not quiet:
                    p(result)
        except Exception as err:  # pylint: disable=broad-except
            p(err)


class rename(Command):
    """:rename <newname>

    Changes the name of the currently highlighted file to <newname>
    """

    def execute(self):
        from ranger.container.file import File
        from os import access

        new_name = self.rest(1)

        if not new_name:
            return self.fm.notify('Syntax: rename <newname>', bad=True)

        if new_name == self.fm.thisfile.relative_path:
            return

        if access(new_name, os.F_OK):
            return self.fm.notify("Can't rename: file already exists!", bad=True)

        if self.fm.rename(self.fm.thisfile, new_name):
            file_new = File(new_name)
            self.fm.bookmarks.update_path(self.fm.thisfile.path, file_new)
            self.fm.tags.update_path(self.fm.thisfile.path, file_new.path)
            self.fm.thisdir.pointed_obj = file_new
            self.fm.thisfile = file_new

    def tab(self, tabnum):
        return self._tab_directory_content()


class rename_append(Command):
    """:rename_append [-FLAGS...]

    Opens the console with ":rename <current file>" with the cursor positioned
    before the file extension.

    Flags:
     -a    Position before all extensions
     -r    Remove everything before extensions
    """
    def __init__(self, *args, **kwargs):
        super(rename_append, self).__init__(*args, **kwargs)

        flags, _ = self.parse_flags()
        self._flag_ext_all = 'a' in flags
        self._flag_remove = 'r' in flags

    def execute(self):
        from ranger import MACRO_DELIMITER, MACRO_DELIMITER_ESC

        tfile = self.fm.thisfile
        relpath = tfile.relative_path.replace(MACRO_DELIMITER, MACRO_DELIMITER_ESC)
        basename = tfile.basename.replace(MACRO_DELIMITER, MACRO_DELIMITER_ESC)

        if basename.find('.') <= 0:
            self.fm.open_console('rename ' + relpath)
            return

        if self._flag_ext_all:
            pos_ext = re.search(r'[^.]+', basename).end(0)
        else:
            pos_ext = basename.rindex('.')
        pos = len(relpath) - len(basename) + pos_ext

        if self._flag_remove:
            relpath = relpath[:-len(basename)] + basename[pos_ext:]
            pos -= pos_ext

        self.fm.open_console('rename ' + relpath, position=(7 + pos))


class chmod(Command):
    """:chmod <octal number>

    Sets the permissions of the selection to the octal number.

    The octal number is between 0 and 777. The digits specify the
    permissions for the user, the group and others.

    A 1 permits execution, a 2 permits writing, a 4 permits reading.
    Add those numbers to combine them. So a 7 permits everything.
    """

    def execute(self):
        mode_str = self.rest(1)
        if not mode_str:
            mode_str = str(self.quantifier)

        try:
            mode = int(mode_str, 8)
            if mode < 0 or mode > 0o777:
                raise ValueError
        except ValueError:
            self.fm.notify("Need an octal number between 0 and 777!", bad=True)
            return

        for fobj in self.fm.thistab.get_selection():
            try:
                os.chmod(fobj.path, mode)
            except OSError as ex:
                self.fm.notify(ex)

        # reloading directory.  maybe its better to reload the selected
        # files only.
        self.fm.thisdir.content_outdated = True


class bulkrename(Command):
    """:bulkrename

    This command opens a list of selected files in an external editor.
    After you edit and save the file, it will generate a shell script
    which does bulk renaming according to the changes you did in the file.

    This shell script is opened in an editor for you to review.
    After you close it, it will be executed.
    """

    def execute(self):  # pylint: disable=too-many-locals,too-many-statements
        import sys
        import tempfile
        from ranger.container.file import File
        from ranger.ext.shell_escape import shell_escape as esc
        py3 = sys.version_info[0] >= 3

        # Create and edit the file list
        filenames = [f.relative_path for f in self.fm.thistab.get_selection()]
        listfile = tempfile.NamedTemporaryFile(delete=False)
        listpath = listfile.name

        if py3:
            listfile.write("\n".join(filenames).encode("utf-8"))
        else:
            listfile.write("\n".join(filenames))
        listfile.close()
        self.fm.execute_file([File(listpath)], app='editor')
        listfile = open(listpath, 'r')
        new_filenames = listfile.read().split("\n")
        listfile.close()
        os.unlink(listpath)
        if all(a == b for a, b in zip(filenames, new_filenames)):
            self.fm.notify("No renaming to be done!")
            return

        # Generate script
        cmdfile = tempfile.NamedTemporaryFile()
        script_lines = []
        script_lines.append("# This file will be executed when you close the editor.\n")
        script_lines.append("# Please double-check everything, clear the file to abort.\n")
        script_lines.extend("mv -vi -- %s %s\n" % (esc(old), esc(new))
                            for old, new in zip(filenames, new_filenames) if old != new)
        script_content = "".join(script_lines)
        if py3:
            cmdfile.write(script_content.encode("utf-8"))
        else:
            cmdfile.write(script_content)
        cmdfile.flush()

        # Open the script and let the user review it, then check if the script
        # was modified by the user
        self.fm.execute_file([File(cmdfile.name)], app='editor')
        cmdfile.seek(0)
        script_was_edited = (script_content != cmdfile.read())

        # Do the renaming
        self.fm.run(['/bin/sh', cmdfile.name], flags='w')
        cmdfile.close()

        # Retag the files, but only if the script wasn't changed during review,
        # because only then we know which are the source and destination files.
        if not script_was_edited:
            tags_changed = False
            for old, new in zip(filenames, new_filenames):
                if old != new:
                    oldpath = self.fm.thisdir.path + '/' + old
                    newpath = self.fm.thisdir.path + '/' + new
                    if oldpath in self.fm.tags:
                        old_tag = self.fm.tags.tags[oldpath]
                        self.fm.tags.remove(oldpath)
                        self.fm.tags.tags[newpath] = old_tag
                        tags_changed = True
            if tags_changed:
                self.fm.tags.dump()
        else:
            fm.notify("files have not been retagged")


class relink(Command):
    """:relink <newpath>

    Changes the linked path of the currently highlighted symlink to <newpath>
    """

    def execute(self):
        new_path = self.rest(1)
        tfile = self.fm.thisfile

        if not new_path:
            return self.fm.notify('Syntax: relink <newpath>', bad=True)

        if not tfile.is_link:
            return self.fm.notify('%s is not a symlink!' % tfile.relative_path, bad=True)

        if new_path == os.readlink(tfile.path):
            return

        try:
            os.remove(tfile.path)
            os.symlink(new_path, tfile.path)
        except OSError as err:
            self.fm.notify(err)

        self.fm.reset()
        self.fm.thisdir.pointed_obj = tfile
        self.fm.thisfile = tfile

    def tab(self, tabnum):
        if not self.rest(1):
            return self.line + os.readlink(self.fm.thisfile.path)
        return self._tab_directory_content()


class help_(Command):
    """:help

    Display ranger's manual page.
    """
    name = 'help'

    def execute(self):
        def callback(answer):
            if answer == "q":
                return
            elif answer == "m":
                self.fm.display_help()
            elif answer == "c":
                self.fm.dump_commands()
            elif answer == "k":
                self.fm.dump_keybindings()
            elif answer == "s":
                self.fm.dump_settings()

        self.fm.ui.console.ask(
            "View [m]an page, [k]ey bindings, [c]ommands or [s]ettings? (press q to abort)",
            callback,
            list("mkcsq") + [chr(27)]
        )


class copymap(Command):
    """:copymap <keys> <newkeys1> [<newkeys2>...]

    Copies a "browser" keybinding from <keys> to <newkeys>
    """
    context = 'browser'

    def execute(self):
        if not self.arg(1) or not self.arg(2):
            return self.fm.notify("Not enough arguments", bad=True)

        for arg in self.args[2:]:
            self.fm.ui.keymaps.copy(self.context, self.arg(1), arg)


class copypmap(copymap):
    """:copypmap <keys> <newkeys1> [<newkeys2>...]

    Copies a "pager" keybinding from <keys> to <newkeys>
    """
    context = 'pager'


class copycmap(copymap):
    """:copycmap <keys> <newkeys1> [<newkeys2>...]

    Copies a "console" keybinding from <keys> to <newkeys>
    """
    context = 'console'


class copytmap(copymap):
    """:copycmap <keys> <newkeys1> [<newkeys2>...]

    Copies a "taskview" keybinding from <keys> to <newkeys>
    """
    context = 'taskview'


class unmap(Command):
    """:unmap <keys> [<keys2>, ...]

    Remove the given "browser" mappings
    """
    context = 'browser'

    def execute(self):
        for arg in self.args[1:]:
            self.fm.ui.keymaps.unbind(self.context, arg)


class cunmap(unmap):
    """:cunmap <keys> [<keys2>, ...]

    Remove the given "console" mappings
    """
    context = 'browser'


class punmap(unmap):
    """:punmap <keys> [<keys2>, ...]

    Remove the given "pager" mappings
    """
    context = 'pager'


class tunmap(unmap):
    """:tunmap <keys> [<keys2>, ...]

    Remove the given "taskview" mappings
    """
    context = 'taskview'


class map_(Command):
    """:map <keysequence> <command>

    Maps a command to a keysequence in the "browser" context.

    Example:
    map j move down
    map J move down 10
    """
    name = 'map'
    context = 'browser'
    resolve_macros = False

    def execute(self):
        if not self.arg(1) or not self.arg(2):
            return self.fm.notify("Not enough arguments", bad=True)

        self.fm.ui.keymaps.bind(self.context, self.arg(1), self.rest(2))


class cmap(map_):
    """:cmap <keysequence> <command>

    Maps a command to a keysequence in the "console" context.

    Example:
    cmap <ESC> console_close
    cmap <C-x> console_type test
    """
    context = 'console'


class tmap(map_):
    """:tmap <keysequence> <command>

    Maps a command to a keysequence in the "taskview" context.
    """
    context = 'taskview'


class pmap(map_):
    """:pmap <keysequence> <command>

    Maps a command to a keysequence in the "pager" context.
    """
    context = 'pager'


class scout(Command):
    """:scout [-FLAGS...] <pattern>

    Swiss army knife command for searching, traveling and filtering files.

    Flags:
     -a    Automatically open a file on unambiguous match
     -e    Open the selected file when pressing enter
     -f    Filter files that match the current search pattern
     -g    Interpret pattern as a glob pattern
     -i    Ignore the letter case of the files
     -k    Keep the console open when changing a directory with the command
     -l    Letter skipping; e.g. allow "rdme" to match the file "readme"
     -m    Mark the matching files after pressing enter
     -M    Unmark the matching files after pressing enter
     -p    Permanent filter: hide non-matching files after pressing enter
     -r    Interpret pattern as a regular expression pattern
     -s    Smart case; like -i unless pattern contains upper case letters
     -t    Apply filter and search pattern as you type
     -v    Inverts the match

    Multiple flags can be combined.  For example, ":scout -gpt" would create
    a :filter-like command using globbing.
    """
    # pylint: disable=bad-whitespace
    AUTO_OPEN     = 'a'
    OPEN_ON_ENTER = 'e'
    FILTER        = 'f'
    SM_GLOB       = 'g'
    IGNORE_CASE   = 'i'
    KEEP_OPEN     = 'k'
    SM_LETTERSKIP = 'l'
    MARK          = 'm'
    UNMARK        = 'M'
    PERM_FILTER   = 'p'
    SM_REGEX      = 'r'
    SMART_CASE    = 's'
    AS_YOU_TYPE   = 't'
    INVERT        = 'v'
    # pylint: enable=bad-whitespace

    def __init__(self, *args, **kwargs):
        super(scout, self).__init__(*args, **kwargs)
        self._regex = None
        self.flags, self.pattern = self.parse_flags()

    def execute(self):  # pylint: disable=too-many-branches
        thisdir = self.fm.thisdir
        flags = self.flags
        pattern = self.pattern
        regex = self._build_regex()
        count = self._count(move=True)

        self.fm.thistab.last_search = regex
        self.fm.set_search_method(order="search")

        if (self.MARK in flags or self.UNMARK in flags) and thisdir.files:
            value = flags.find(self.MARK) > flags.find(self.UNMARK)
            if self.FILTER in flags:
                for fobj in thisdir.files:
                    thisdir.mark_item(fobj, value)
            else:
                for fobj in thisdir.files:
                    if regex.search(fobj.relative_path):
                        thisdir.mark_item(fobj, value)

        if self.PERM_FILTER in flags:
            thisdir.filter = regex if pattern else None

        # clean up:
        self.cancel()

        if self.OPEN_ON_ENTER in flags or \
                (self.AUTO_OPEN in flags and count == 1):
            self.fm.move(right=1)

        if self.KEEP_OPEN in flags and thisdir != self.fm.thisdir:
            # reopen the console:
            if not pattern:
                self.fm.open_console(self.line)
            else:
                self.fm.open_console(self.line[0:-len(pattern)])

        if self.quickly_executed and thisdir != self.fm.thisdir and pattern != "..":
            self.fm.block_input(0.5)

    def cancel(self):
        self.fm.thisdir.temporary_filter = None
        self.fm.thisdir.refilter()

    def quick(self):
        asyoutype = self.AS_YOU_TYPE in self.flags
        if self.FILTER in self.flags:
            self.fm.thisdir.temporary_filter = self._build_regex()
        if self.PERM_FILTER in self.flags and asyoutype:
            self.fm.thisdir.filter = self._build_regex()
        if self.FILTER in self.flags or self.PERM_FILTER in self.flags:
            self.fm.thisdir.refilter()
        if self._count(move=asyoutype) == 1 and self.AUTO_OPEN in self.flags:
            return True
        return False

    def tab(self, tabnum):
        self._count(move=True, offset=tabnum)

    def _build_regex(self):
        if self._regex is not None:
            return self._regex

        frmat = "%s"
        flags = self.flags
        pattern = self.pattern

        if pattern == ".":
            return re.compile("")

        # Handle carets at start and dollar signs at end separately
        if pattern.startswith('^'):
            pattern = pattern[1:]
            frmat = "^" + frmat
        if pattern.endswith('$'):
            pattern = pattern[:-1]
            frmat += "$"

        # Apply one of the search methods
        if self.SM_REGEX in flags:
            regex = pattern
        elif self.SM_GLOB in flags:
            regex = re.escape(pattern).replace("\\*", ".*").replace("\\?", ".")
        elif self.SM_LETTERSKIP in flags:
            regex = ".*".join(re.escape(c) for c in pattern)
        else:
            regex = re.escape(pattern)

        regex = frmat % regex

        # Invert regular expression if necessary
        if self.INVERT in flags:
            regex = "^(?:(?!%s).)*$" % regex

        # Compile Regular Expression
        # pylint: disable=no-member
        options = re.UNICODE
        if self.IGNORE_CASE in flags or self.SMART_CASE in flags and \
                pattern.islower():
            options |= re.IGNORECASE
        # pylint: enable=no-member
        try:
            self._regex = re.compile(regex, options)
        except re.error:
            self._regex = re.compile("")
        return self._regex

    def _count(self, move=False, offset=0):
        count = 0
        cwd = self.fm.thisdir
        pattern = self.pattern

        if not pattern or not cwd.files:
            return 0
        if pattern == '.':
            return 0
        if pattern == '..':
            return 1

        deq = deque(cwd.files)
        deq.rotate(-cwd.pointer - offset)
        i = offset
        regex = self._build_regex()
        for fsobj in deq:
            if regex.search(fsobj.relative_path):
                count += 1
                if move and count == 1:
                    cwd.move(to=(cwd.pointer + i) % len(cwd.files))
                    self.fm.thisfile = cwd.pointed_obj
            if count > 1:
                return count
            i += 1

        return count == 1


class filter_inode_type(Command):
    """
    :filter_inode_type [dfl]

    Displays only the files of specified inode type. Parameters
    can be combined.

        d display directories
        f display files
        l display links
    """
    # pylint: disable=bad-whitespace
    FILTER_DIRS  = 'd'
    FILTER_FILES = 'f'
    FILTER_LINKS = 'l'
    # pylint: enable=bad-whitespace

    def execute(self):
        if not self.arg(1):
            self.fm.thisdir.inode_type_filter = None
        else:
            self.fm.thisdir.inode_type_filter = lambda file: (
                True if (
                    (self.FILTER_DIRS in self.arg(1) and file.is_directory) or
                    (self.FILTER_FILES in self.arg(1) and file.is_file and not file.is_link) or
                    (self.FILTER_LINKS in self.arg(1) and file.is_link)
                ) else False)
        self.fm.thisdir.refilter()


class grep(Command):
    """:grep <string>

    Looks for a string in all marked files or directories
    """

    def execute(self):
        if self.rest(1):
            action = ['grep', '--line-number']
            action.extend(['-e', self.rest(1), '-r'])
            action.extend(f.path for f in self.fm.thistab.get_selection())
            self.fm.execute_command(action, flags='p')


class flat(Command):
    """
    :flat <level>

    Flattens the directory view up to the specified level.

        -1 fully flattened
         0 remove flattened view
    """

    def execute(self):
        try:
            level_str = self.rest(1)
            level = int(level_str)
        except ValueError:
            level = self.quantifier
        if level < -1:
            self.fm.notify("Need an integer number (-1, 0, 1, ...)", bad=True)
        self.fm.thisdir.unload()
        self.fm.thisdir.flat = level
        self.fm.thisdir.load_content()

# Version control commands
# --------------------------------


class stage(Command):
    """
    :stage

    Stage selected files for the corresponding version control system
    """

    def execute(self):
        from ranger.ext.vcs import VcsError

        if self.fm.thisdir.vcs and self.fm.thisdir.vcs.track:
            filelist = [f.path for f in self.fm.thistab.get_selection()]
            try:
                self.fm.thisdir.vcs.action_add(filelist)
            except VcsError as error:
                self.fm.notify('Unable to stage files: {0:s}'.format(str(error)))
            self.fm.ui.vcsthread.process(self.fm.thisdir)
        else:
            self.fm.notify('Unable to stage files: Not in repository')


class unstage(Command):
    """
    :unstage

    Unstage selected files for the corresponding version control system
    """

    def execute(self):
        from ranger.ext.vcs import VcsError

        if self.fm.thisdir.vcs and self.fm.thisdir.vcs.track:
            filelist = [f.path for f in self.fm.thistab.get_selection()]
            try:
                self.fm.thisdir.vcs.action_reset(filelist)
            except VcsError as error:
                self.fm.notify('Unable to unstage files: {0:s}'.format(str(error)))
            self.fm.ui.vcsthread.process(self.fm.thisdir)
        else:
            self.fm.notify('Unable to unstage files: Not in repository')

# Metadata commands
# --------------------------------


class prompt_metadata(Command):
    """
    :prompt_metadata <key1> [<key2> [<key3> ...]]

    Prompt the user to input metadata for multiple keys in a row.
    """

    _command_name = "meta"
    _console_chain = None

    def execute(self):
        prompt_metadata._console_chain = self.args[1:]
        self._process_command_stack()

    def _process_command_stack(self):
        if prompt_metadata._console_chain:
            key = prompt_metadata._console_chain.pop()
            self._fill_console(key)
        else:
            for col in self.fm.ui.browser.columns:
                col.need_redraw = True

    def _fill_console(self, key):
        metadata = self.fm.metadata.get_metadata(self.fm.thisfile.path)
        if key in metadata and metadata[key]:
            existing_value = metadata[key]
        else:
            existing_value = ""
        text = "%s %s %s" % (self._command_name, key, existing_value)
        self.fm.open_console(text, position=len(text))


class meta(prompt_metadata):
    """
    :meta <key> [<value>]

    Change metadata of a file.  Deletes the key if value is empty.
    """

    def execute(self):
        key = self.arg(1)
        update_dict = dict()
        update_dict[key] = self.rest(2)
        selection = self.fm.thistab.get_selection()
        for fobj in selection:
            self.fm.metadata.set_metadata(fobj.path, update_dict)
        self._process_command_stack()

    def tab(self, tabnum):
        key = self.arg(1)
        metadata = self.fm.metadata.get_metadata(self.fm.thisfile.path)
        if key in metadata and metadata[key]:
            return [" ".join([self.arg(0), self.arg(1), metadata[key]])]
        return [self.arg(0) + " " + k for k in sorted(metadata)
                if k.startswith(self.arg(1))]


class linemode(default_linemode):
    """
    :linemode <mode>

    Change what is displayed as a filename.

    - "mode" may be any of the defined linemodes (see: ranger.core.linemode).
      "normal" is mapped to "filename".
    """

    def execute(self):
        mode = self.arg(1)

        if mode == "normal":
            from ranger.core.linemode import DEFAULT_LINEMODE
            mode = DEFAULT_LINEMODE

        if mode not in self.fm.thisfile.linemode_dict:
            self.fm.notify("Unhandled linemode: `%s'" % mode, bad=True)
            return

        self.fm.thisdir.set_linemode_of_children(mode)

        # Ask the browsercolumns to redraw
        for col in self.fm.ui.browser.columns:
            col.need_redraw = True
