# -*- coding: utf-8 -*-
# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This configuration file is licensed under the same terms as ranger.
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
#   execute(): called when the command is executed.
#   cancel():  called when closing the console.
#   tab():     called when <TAB> is pressed.
#   quick():   called after each keypress.
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
#      If the command was "search foo bar a b c", rest(2) will be "bar a b c"
# self.start(n): The n-th argument and anything before it.  For example,
#      If the command was "search foo bar a b c", rest(2) will be "bar a b c"
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
# cf.path: The path to the file.
# cf.basename: The base name only.
# cf.load_content(): Force a loading of the directories content (which
#      obviously works with directories only)
# cf.is_directory: True/False depending on whether it's a directory.
#
# For advanced commands it is unavoidable to dive a bit into the source code
# of ranger.
# ===================================================================

from ranger.api.commands import *

class alias(Command):
    """:alias <newcommand> <oldcommand>

    Copies the oldcommand as newcommand.
    """

    context = 'browser'
    resolve_macros = False

    def execute(self):
        if not self.arg(1) or not self.arg(2):
            self.fm.notify('Syntax: alias <newcommand> <oldcommand>', bad=True)
        else:
            self.fm.commands.alias(self.arg(1), self.rest(2))

class cd(Command):
    """:cd [-r] <dirname>

    The cd command changes the directory.
    The command 'cd -' is equivalent to typing ``.
    Using the option "-r" will get you to the real path.
    """

    def execute(self):
        import os.path
        if self.arg(1) == '-r':
            self.shift()
            destination = os.path.realpath(self.rest(1))
            if os.path.isfile(destination):
                destination = os.path.dirname(destination)
        else:
            destination = self.rest(1)

        if not destination:
            destination = '~'

        if destination == '-':
            self.fm.enter_bookmark('`')
        else:
            self.fm.cd(destination)

    def tab(self):
        import os
        from os.path import dirname, basename, expanduser, join

        cwd = self.fm.thisdir.path
        rel_dest = self.rest(1)

        bookmarks = [v.path for v in self.fm.bookmarks.dct.values()
                if rel_dest in v.path ]

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
                dirnames = [dn for dn in dirnames \
                        if dn.startswith(rel_basename)]
        except (OSError, StopIteration):
            # os.walk found nothing
            pass
        else:
            dirnames.sort()
            dirnames = bookmarks + dirnames

            # no results, return None
            if len(dirnames) == 0:
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
        for command in self.rest(1).split(";"):
            self.fm.execute_console(command)


class search(Command):
    def execute(self):
        self.fm.search_file(self.rest(1), regexp=True)


class search_inc(Command):
    def quick(self):
        self.fm.search_file(self.rest(1), regexp=True, offset=0)


class shell(Command):
    escape_macros_for_shell = True

    def execute(self):
        if self.arg(1) and self.arg(1)[0] == '-':
            flags = self.arg(1)[1:]
            command = self.rest(2)
        else:
            flags = ''
            command = self.rest(1)

        if not command and 'p' in flags:
            command = 'cat %f'
        if command:
            if '%' in command:
                command = self.fm.substitute_macros(command)
            self.fm.execute_command(command, flags=flags)

    def tab(self):
        from ranger.ext.get_executables import get_executables
        if self.arg(1) and self.arg(1)[0] == '-':
            command = self.rest(2)
        else:
            command = self.rest(1)
        start = self.line[0:len(self.line) - len(command)]

        try:
            position_of_last_space = command.rindex(" ")
        except ValueError:
            return (start + program + ' ' for program \
                    in get_executables() if program.startswith(command))
        if position_of_last_space == len(command) - 1:
            selection = self.fm.thistab.get_selection()
            if len(selection) == 1:
                return self.line + selection[0].shell_escaped_basename + ' '
            else:
                return self.line + '%s '
        else:
            before_word, start_of_word = self.line.rsplit(' ', 1)
            return (before_word + ' ' + file.shell_escaped_basename \
                    for file in self.fm.thisdir.files \
                    if file.shell_escaped_basename.startswith(start_of_word))

class open_with(Command):
    def execute(self):
        app, flags, mode = self._get_app_flags_mode(self.rest(1))
        self.fm.execute_file(
                files = [f for f in self.fm.thistab.get_selection()],
                app = app,
                flags = flags,
                mode = mode)

    def tab(self):
        return self._tab_through_executables()

    def _get_app_flags_mode(self, string):
        """Extracts the application, flags and mode from a string.

        examples:
        "mplayer f 1" => ("mplayer", "f", 1)
        "aunpack 4" => ("aunpack", "", 4)
        "p" => ("", "p", 0)
        "" => None
        """

        app = ''
        flags = ''
        mode = 0
        split = string.split()

        if len(split) == 0:
            pass

        elif len(split) == 1:
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

    def _is_flags(self, arg):
        from ranger.core.runner import ALLOWED_FLAGS
        return all(x in ALLOWED_FLAGS for x in arg)

    def _is_mode(self, arg):
        return all(x in '0123456789' for x in arg)


class find(Command):
    """:find <string>

    The find command will attempt to find a partial, case insensitive
    match in the filenames of the current directory and execute the
    file automatically.
    """

    count = 0
    tab = Command._tab_directory_content

    def execute(self):
        if self.quick():
            if self.rest(1) == '..':
                self.fm.move(left=1)
            else:
                self.fm.move(right=1)
            self.fm.block_input(0.5)
        else:
            self.fm.cd(self.rest(1))

    def quick(self):
        self.count = 0
        cwd = self.fm.thisdir
        arg = self.rest(1)
        if not arg:
            return False

        if arg == '.':
            return False
        if arg == '..':
            return True

        deq = deque(cwd.files)
        deq.rotate(-cwd.pointer)
        i = 0
        case_insensitive = arg.lower() == arg
        for fsobj in deq:
            if case_insensitive:
                filename = fsobj.basename_lower
            else:
                filename = fsobj.basename
            if arg in filename:
                self.count += 1
                if self.count == 1:
                    cwd.move(to=(cwd.pointer + i) % len(cwd.files))
                    self.fm.thisfile = cwd.pointed_obj
            if self.count > 1:
                return False
            i += 1

        return self.count == 1


class set_(Command):
    """:set <option name>=<python expression>

    Gives an option a new value.
    """
    name = 'set'  # don't override the builtin set class
    def execute(self):
        name = self.arg(1)
        name, value, _ = self.parse_setting_line()
        self.fm.set_option_from_string(name, value)

    def tab(self):
        name, value, name_done = self.parse_setting_line()
        settings = self.fm.settings
        if not name:
            return sorted(self.firstpart + setting for setting in settings)
        if not value and not name_done:
            return (self.firstpart + setting for setting in settings \
                    if setting.startswith(name))
        if not value:
            return self.firstpart + str(settings[name])
        if bool in settings.types_of(name):
            if 'true'.startswith(value.lower()):
                return self.firstpart + 'True'
            if 'false'.startswith(value.lower()):
                return self.firstpart + 'False'


class setlocal(set_):
    """:setlocal path=<python string> <option name>=<python expression>

    Gives an option a new value.
    """
    PATH_RE = re.compile(r'^\s*path="?(.*?)"?\s*$')
    def execute(self):
        import os.path
        match = self.PATH_RE.match(self.arg(1))
        if match:
            path = os.path.normpath(os.path.expanduser(match.group(1)))
            self.shift()
        elif self.fm.thisdir:
            path = self.fm.thisdir.path
        else:
            path = None

        if path:
            name = self.arg(1)
            name, value, _ = self.parse_setting_line()
            self.fm.set_option_from_string(name, value, localpath=path)


class quit(Command):
    """:quit

    Closes the current tab.  If there is only one tab, quit the program.
    """

    def execute(self):
        if len(self.fm.tabs) <= 1:
            self.fm.exit()
        self.fm.tab_close()


class quitall(Command):
    """:quitall

    Quits the program immediately.
    """

    def execute(self):
        self.fm.exit()


class quit_bang(quitall):
    """:quit!

    Quits the program immediately.
    """
    name = 'quit!'
    allow_abbrev = False


class terminal(Command):
    """:terminal

    Spawns an "x-terminal-emulator" starting in the current directory.
    """
    def execute(self):
        import os
        from ranger.ext.get_executables import get_executables
        command = os.environ.get('TERMCMD', os.environ.get('TERM'))
        if command not in get_executables():
            command = 'x-terminal-emulator'
        if command not in get_executables():
            command = 'xterm'
        self.fm.run(command, flags='f')


class delete(Command):
    """:delete

    Tries to delete the selection.

    "Selection" is defined as all the "marked files" (by default, you
    can mark files with space or v). If there are no marked files,
    use the "current file" (where the cursor is)

    When attempting to delete non-empty directories or multiple
    marked files, it will require a confirmation.
    """

    allow_abbrev = False

    def execute(self):
        import os
        if self.rest(1):
            self.fm.notify("Error: delete takes no arguments! It deletes "
                    "the selected file(s).", bad=True)
            return

        cwd = self.fm.thisdir
        cf = self.fm.thisfile
        if not cwd or not cf:
            self.fm.notify("Error: no file selected for deletion!", bad=True)
            return

        confirm = self.fm.settings.confirm_on_delete
        many_files = (cwd.marked_items or (cf.is_directory and not cf.is_link \
                and len(os.listdir(cf.path)) > 0))

        if confirm != 'never' and (confirm != 'multiple' or many_files):
            self.fm.ui.console.ask("Confirm deletion of: %s (y/N)" %
                ', '.join(f.basename for f in self.fm.thistab.get_selection()),
                self._question_callback, ('n', 'N', 'y', 'Y'))
        else:
            # no need for a confirmation, just delete
            self.fm.delete()

    def _question_callback(self, answer):
        if answer == 'y' or answer == 'Y':
            self.fm.delete()


class mark(Command):
    """:mark <regexp>

    Mark all files matching a regular expression.
    """
    do_mark = True

    def execute(self):
        import re
        cwd = self.fm.thisdir
        input = self.rest(1)
        searchflags = re.UNICODE
        if input.lower() == input: # "smartcase"
            searchflags |= re.IGNORECASE
        pattern = re.compile(input, searchflags)
        for fileobj in cwd.files:
            if pattern.search(fileobj.basename):
                cwd.mark_item(fileobj, val=self.do_mark)
        self.fm.ui.status.need_redraw = True
        self.fm.ui.need_redraw = True


class mark_tag(Command):
    """:mark_tag [<tags>]

    Mark all tags that are tagged with either of the given tags.
    When leaving out the tag argument, all tagged files are marked.
    """
    do_mark = True

    def execute(self):
        cwd = self.fm.thisdir
        tags = self.rest(1).replace(" ","")
        if not self.fm.tags:
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
                self.shift()
            except:
                pass
        self.fm.open_console(self.rest(1), position=position)


class load_copy_buffer(Command):
    """:load_copy_buffer

    Load the copy buffer from confdir/copy_buffer
    """
    copy_buffer_filename = 'copy_buffer'
    def execute(self):
        from ranger.fsobject import File
        from os.path import exists
        try:
            fname = self.fm.confpath(self.copy_buffer_filename)
            f = open(fname, 'r')
        except:
            return self.fm.notify("Cannot open %s" % \
                    (fname or self.copy_buffer_filename), bad=True)
        self.fm.copy_buffer = set(File(g) \
            for g in f.read().split("\n") if exists(g))
        f.close()
        self.fm.ui.redraw_main_column()


class save_copy_buffer(Command):
    """:save_copy_buffer

    Save the copy buffer to confdir/copy_buffer
    """
    copy_buffer_filename = 'copy_buffer'
    def execute(self):
        fname = None
        try:
            fname = self.fm.confpath(self.copy_buffer_filename)
            f = open(fname, 'w')
        except:
            return self.fm.notify("Cannot open %s" % \
                    (fname or self.copy_buffer_filename), bad=True)
        f.write("\n".join(f.path for f in self.fm.copy_buffer))
        f.close()


class unmark(mark):
    """:unmark <regexp>

    Unmark all files matching a regular expression.
    """
    do_mark = False


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
        from os import mkdir

        dirname = join(self.fm.thisdir.path, expanduser(self.rest(1)))
        if not lexists(dirname):
            mkdir(dirname)
        else:
            self.fm.notify("file/directory exists!", bad=True)

    def tab(self):
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

    def tab(self):
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

    def tab(self):
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
        import ranger
        global cmd, fm, p, quantifier
        fm = self.fm
        cmd = self.fm.execute_console
        p = fm.notify
        quantifier = self.quantifier
        try:
            try:
                result = eval(code)
            except SyntaxError:
                exec(code)
            else:
                if result and not quiet:
                    p(result)
        except Exception as err:
            p(err)


class rename(Command):
    """:rename <newname>

    Changes the name of the currently highlighted file to <newname>
    """

    def execute(self):
        from ranger.fsobject import File
        from os import access

        new_name = self.rest(1)

        if not new_name:
            return self.fm.notify('Syntax: rename <newname>', bad=True)

        if new_name == self.fm.thisfile.basename:
            return

        if access(new_name, os.F_OK):
            return self.fm.notify("Can't rename: file already exists!", bad=True)

        self.fm.rename(self.fm.thisfile, new_name)
        f = File(new_name)
        self.fm.thisdir.pointed_obj = f
        self.fm.thisfile = f

    def tab(self):
        return self._tab_directory_content()


class chmod(Command):
    """:chmod <octal number>

    Sets the permissions of the selection to the octal number.

    The octal number is between 0 and 777. The digits specify the
    permissions for the user, the group and others.

    A 1 permits execution, a 2 permits writing, a 4 permits reading.
    Add those numbers to combine them. So a 7 permits everything.
    """

    def execute(self):
        mode = self.rest(1)
        if not mode:
            mode = str(self.quantifier)

        try:
            mode = int(mode, 8)
            if mode < 0 or mode > 0o777:
                raise ValueError
        except ValueError:
            self.fm.notify("Need an octal number between 0 and 777!", bad=True)
            return

        for file in self.fm.thistab.get_selection():
            try:
                os.chmod(file.path, mode)
            except Exception as ex:
                self.fm.notify(ex)

        try:
            # reloading directory.  maybe its better to reload the selected
            # files only.
            self.fm.thisdir.load_content()
        except:
            pass


class bulkrename(Command):
    """:bulkrename

    This command opens a list of selected files in an external editor.
    After you edit and save the file, it will generate a shell script
    which does bulk renaming according to the changes you did in the file.

    This shell script is opened in an editor for you to review.
    After you close it, it will be executed.
    """
    def execute(self):
        import sys
        import tempfile
        from ranger.fsobject.file import File
        from ranger.ext.shell_escape import shell_escape as esc
        py3 = sys.version > "3"

        # Create and edit the file list
        filenames = [f.basename for f in self.fm.thistab.get_selection()]
        listfile = tempfile.NamedTemporaryFile()

        if py3:
            listfile.write("\n".join(filenames).encode("utf-8"))
        else:
            listfile.write("\n".join(filenames))
        listfile.flush()
        self.fm.execute_file([File(listfile.name)], app='editor')
        listfile.seek(0)
        if py3:
            new_filenames = listfile.read().decode("utf-8").split("\n")
        else:
            new_filenames = listfile.read().split("\n")
        listfile.close()
        if all(a == b for a, b in zip(filenames, new_filenames)):
            self.fm.notify("No renaming to be done!")
            return

        # Generate and execute script
        cmdfile = tempfile.NamedTemporaryFile()
        cmdfile.write(b"# This file will be executed when you close the editor.\n")
        cmdfile.write(b"# Please double-check everything, clear the file to abort.\n")
        if py3:
            cmdfile.write("\n".join("mv -vi -- " + esc(old) + " " + esc(new) \
                for old, new in zip(filenames, new_filenames) \
                if old != new).encode("utf-8"))
        else:
            cmdfile.write("\n".join("mv -vi -- " + esc(old) + " " + esc(new) \
                for old, new in zip(filenames, new_filenames) if old != new))
        cmdfile.flush()
        self.fm.execute_file([File(cmdfile.name)], app='editor')
        self.fm.run(['/bin/sh', cmdfile.name], flags='w')
        cmdfile.close()


class relink(Command):
    """:relink <newpath>

    Changes the linked path of the currently highlighted symlink to <newpath>
    """

    def execute(self):
        from ranger.fsobject import File

        new_path = self.rest(1)
        cf = self.fm.thisfile

        if not new_path:
            return self.fm.notify('Syntax: relink <newpath>', bad=True)

        if not cf.is_link:
            return self.fm.notify('%s is not a symlink!' % cf.basename, bad=True)

        if new_path == os.readlink(cf.path):
            return

        try:
            os.remove(cf.path)
            os.symlink(new_path, cf.path)
        except OSError as err:
            self.fm.notify(err)

        self.fm.reset()
        self.fm.thisdir.pointed_obj = cf
        self.fm.thisfile = cf

    def tab(self):
        if not self.rest(1):
            return self.line+os.readlink(self.fm.thisfile.path)
        else:
            return self._tab_directory_content()


class help_(Command):
    """:help

    Display ranger's manual page.
    """
    name = 'help'
    def execute(self):
        if self.quantifier == 1:
            self.fm.dump_keybindings()
        elif self.quantifier == 2:
            self.fm.dump_commands()
        elif self.quantifier == 3:
            self.fm.dump_settings()
        else:
            self.fm.display_help()


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


class travel(Command):
    """:travel <string>

    Filters the current directory for files containing the letters in the
    string, possibly with other letters in between.  The filter is applied as
    you type.  When only one directory is left, it is entered and the console
    is automatially reopened, allowing for fast travel.
    To close the console, press ESC or execute a file.
    """

    def execute(self):
        thisdir = self.fm.thisdir

        self.cancel() # Clean up
        if self.rest(1) == "..":
            self.fm.move(left=1)
        elif len(thisdir.files) > 0:
            self.fm.move(right=1)
        else:
            self.fm.cd(self.rest(1))

        # reopen the console:
        if thisdir != self.fm.thisdir:
            self.fm.open_console(self.__class__.__name__ + " ")
            if self.rest(1) != "..":
                self.fm.block_input(0.5)

    def cancel(self):
        self.fm.thisdir.temporary_filter = None
        self.fm.thisdir.load_content(schedule=False)

    def quick(self):
        self.fm.thisdir.temporary_filter = self.build_regex(self.rest(1))
        self.fm.thisdir.load_content(schedule=False)
        arg = self.rest(1)

        if arg == ".":
            return False # Make sure we can always use ".."
        elif arg and len(self.fm.thisdir.files) == 1 or arg == "..":
            return True

    def tab(self):
        if self.fm.thisdir.files[-1] is not self.fm.thisfile:
            self.fm.move(down=1)
        else:
            # We're at the bottom, so wrap
            self.fm.move(to=0)

    def build_regex(self, arg):
        regex = "%s"
        if arg.endswith("$"):
            arg = arg[:-1]
            regex += "$"
        if arg.startswith("^"):
            arg = arg[1:]
            regex = "^" + regex

        case_insensitive = arg.lower() == arg
        flags = re.I if case_insensitive else 0
        return re.compile(regex % ".*".join(arg), flags)


class filter(Command):
    """:filter <string>

    Displays only the files which contain <string> in their basename.
    """

    def execute(self):
        self.fm.set_filter(self.rest(1))
        self.fm.reload_cwd()

    quick = execute


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
