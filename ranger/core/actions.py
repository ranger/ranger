# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

# pylint: disable=too-many-lines,attribute-defined-outside-init

from __future__ import (absolute_import, division, print_function)

import codecs
import os
from os import link, symlink, listdir, stat
from os.path import join, isdir, realpath, exists
import re
import shlex
import shutil
import string
import tempfile
from inspect import cleandoc
from stat import S_IEXEC
from hashlib import sha1
from sys import version_info
from logging import getLogger

import ranger
from ranger.ext.direction import Direction
from ranger.ext.relative_symlink import relative_symlink
from ranger.ext.keybinding_parser import key_to_string, construct_keybinding
from ranger.ext.shell_escape import shell_quote
from ranger.ext.next_available_filename import next_available_filename
from ranger.ext.rifle import squash_flags, ASK_COMMAND
from ranger.core.shared import FileManagerAware, SettingsAware
from ranger.core.tab import Tab
from ranger.container.directory import Directory
from ranger.container.file import File
from ranger.core.loader import CommandLoader, CopyLoader
from ranger.container.settings import ALLOWED_SETTINGS, ALLOWED_VALUES


MACRO_FAIL = "<\x01\x01MACRO_HAS_NO_VALUE\x01\01>"

LOG = getLogger(__name__)


class _MacroTemplate(string.Template):
    """A template for substituting macros in commands"""
    delimiter = ranger.MACRO_DELIMITER
    idpattern = r"[_a-z0-9]*"


class Actions(  # pylint: disable=too-many-instance-attributes,too-many-public-methods
        FileManagerAware, SettingsAware):

    # --------------------------
    # -- Basic Commands
    # --------------------------

    @staticmethod
    def exit():
        """:exit

        Exit the program.
        """
        raise SystemExit

    def reset(self):
        """:reset

        Reset the filemanager, clearing the directory buffer, reload rifle config
        """
        old_path = self.thisdir.path
        self.previews = {}
        self.garbage_collect(-1)
        self.enter_dir(old_path)
        self.change_mode('normal')
        if self.metadata:
            self.metadata.reset()
        self.rifle.reload_config()
        self.fm.tags.sync()

    def change_mode(self, mode=None):
        """:change_mode <mode>

        Change mode to "visual" (selection) or "normal" mode.
        """
        if mode is None:
            self.fm.notify('Syntax: change_mode <mode>', bad=True)
            return
        if mode == self.mode:  # pylint: disable=access-member-before-definition
            return
        if mode == 'visual':
            self._visual_pos_start = self.thisdir.pointer
            self._visual_move_cycles = 0
            self._previous_selection = set(self.thisdir.marked_items)
            self.mark_files(val=not self._visual_reverse, movedown=False)
        elif mode == 'normal':
            if self.mode == 'visual':  # pylint: disable=access-member-before-definition
                self._visual_pos_start = None
                self._visual_move_cycles = None
                self._previous_selection = None
        else:
            return
        self.mode = mode
        self.ui.status.request_redraw()

    def set_option_from_string(self, option_name, value, localpath=None, tags=None):
        if option_name not in ALLOWED_SETTINGS:
            raise ValueError("The option named `%s' does not exist" % option_name)
        if not isinstance(value, str):
            raise ValueError("The value for an option needs to be a string.")

        self.settings.set(option_name, self._parse_option_value(option_name, value),
                          localpath, tags)

    def _parse_option_value(  # pylint: disable=too-many-return-statements
            self, name, value):
        types = self.fm.settings.types_of(name)
        if bool in types:
            if value.lower() in ('false', 'off', '0'):
                return False
            elif value.lower() in ('true', 'on', '1'):
                return True
        if isinstance(None, types) and value.lower() == 'none':
            return None
        if int in types:
            try:
                return int(value)
            except ValueError:
                pass
        if float in types:
            try:
                return float(value)
            except ValueError:
                pass
        if str in types:
            return value
        if list in types:
            return value.split(',')
        raise ValueError("Invalid value `%s' for option `%s'!" % (name, value))

    def toggle_visual_mode(self, reverse=False, narg=None):
        """:toggle_visual_mode

        Toggle the visual mode (see :change_mode).
        """
        if self.mode == 'normal':
            self._visual_reverse = reverse
            if narg is not None:
                self.mark_files(val=not reverse, narg=narg)
            self.change_mode('visual')
        else:
            self.change_mode('normal')

    def reload_cwd(self):
        """:reload_cwd

        Reload the current working directory.
        """
        try:
            cwd = self.thisdir
        except AttributeError:
            pass
        else:
            cwd.unload()
            cwd.load_content()

    def notify(self, obj, duration=4, bad=False, exception=None):
        """:notify <text>

        Display the text in the statusbar.
        """
        if isinstance(obj, Exception):
            if ranger.args.debug:
                raise obj
            exception = obj
            bad = True
        elif bad and ranger.args.debug:
            raise Exception(str(obj))

        text = str(obj)

        text_log = 'Notification: {0}'.format(text)
        if bad:
            LOG.error(text_log)
        else:
            LOG.info(text_log)
        if exception:
            LOG.exception(exception)

        if self.ui and self.ui.is_on:
            self.ui.status.notify("  ".join(text.split("\n")),
                                  duration=duration, bad=bad)
        else:
            print(text)

    def abort(self):
        """:abort

        Empty the first queued action.
        """
        try:
            item = self.loader.queue[0]
        except IndexError:
            self.notify("Type Q or :quit<Enter> to exit ranger")
        else:
            self.notify("Aborting: " + item.get_description())
            self.loader.remove(index=0)

    def get_cumulative_size(self):
        for fobj in self.thistab.get_selection() or ():
            fobj.look_up_cumulative_size()
        self.ui.status.request_redraw()
        self.ui.redraw_main_column()

    def redraw_window(self):
        """:redraw_window

        Redraw the window.
        """
        self.ui.redraw_window()

    def open_console(self, string='',  # pylint: disable=redefined-outer-name
                     prompt=None, position=None):
        """:open_console [string]

        Open the console.
        """
        self.change_mode('normal')
        self.ui.open_console(string, prompt=prompt, position=position)

    def execute_console(self, string='',  # pylint: disable=redefined-outer-name
                        wildcards=None, quantifier=None):
        """:execute_console [string]

        Execute a command for the console
        """
        command_name = string.lstrip().split()[0]
        cmd_class = self.commands.get_command(command_name)
        if cmd_class is None:
            self.notify("Command not found: `%s'" % command_name, bad=True)
            return None
        cmd = cmd_class(string, quantifier=quantifier)

        if cmd.resolve_macros and _MacroTemplate.delimiter in cmd.line:
            def any_macro(i, char):
                return ('any{:d}'.format(i), key_to_string(char))

            def anypath_macro(i, char):
                try:
                    val = self.fm.bookmarks[key_to_string(char)]
                except KeyError:
                    val = MACRO_FAIL
                return ('any_path{:d}'.format(i), val)

            macros = dict(f(i, char) for f in (any_macro, anypath_macro)
                          for i, char in enumerate(wildcards if wildcards
                                                   is not None else []))
            if 'any0' in macros:
                macros['any'] = macros['any0']
                if 'any_path0' in macros:
                    macros['any_path'] = macros['any_path0']
            try:
                line = self.substitute_macros(cmd.line, additional=macros,
                                              escape=cmd.escape_macros_for_shell)
            except ValueError as ex:
                if ranger.args.debug:
                    raise
                return self.notify(ex)
            cmd.init_line(line)

        try:
            cmd.execute()
        except Exception as ex:  # pylint: disable=broad-except
            if ranger.args.debug:
                raise
            self.notify(ex)
        return None

    def substitute_macros(self, string,  # pylint: disable=redefined-outer-name
                          additional=None, escape=False):
        macros = self.get_macros()
        if additional:
            macros.update(additional)
        if escape:
            for key, value in macros.items():
                if isinstance(value, list):
                    macros[key] = " ".join(shell_quote(s) for s in value)
                elif value != MACRO_FAIL:
                    macros[key] = shell_quote(value)
        else:
            for key, value in macros.items():
                if isinstance(value, list):
                    macros[key] = " ".join(value)
        result = _MacroTemplate(string).safe_substitute(macros)
        if MACRO_FAIL in result:
            raise ValueError("Could not apply macros to `%s'" % string)
        return result

    def get_macros(self):  # pylint: disable=too-many-branches,too-many-statements
        macros = {}

        macros['rangerdir'] = ranger.RANGERDIR
        if not ranger.args.clean:
            macros['confdir'] = self.fm.confpath()
            macros['datadir'] = self.fm.datapath()
        macros['space'] = ' '

        if self.fm.thisfile:
            macros['f'] = self.fm.thisfile.relative_path
        else:
            macros['f'] = MACRO_FAIL

        if self.fm.thistab.get_selection:
            macros['p'] = [os.path.join(self.fm.thisdir.path, fl.relative_path)
                           for fl in self.fm.thistab.get_selection()]
            macros['s'] = [fl.relative_path for fl in self.fm.thistab.get_selection()]
        else:
            macros['p'] = MACRO_FAIL
            macros['s'] = MACRO_FAIL

        if self.fm.copy_buffer:
            macros['c'] = [fl.path for fl in self.fm.copy_buffer]
        else:
            macros['c'] = MACRO_FAIL

        if self.fm.thisdir.files:
            macros['t'] = [fl.relative_path for fl in self.fm.thisdir.files
                           if fl.realpath in self.fm.tags or []]
        else:
            macros['t'] = MACRO_FAIL

        if self.fm.thisdir:
            macros['d'] = self.fm.thisdir.path
        else:
            macros['d'] = '.'

        # define d/f/p/s macros for each tab
        for i in range(1, 10):
            try:
                tab = self.fm.tabs[i]
            except KeyError:
                continue
            tabdir = tab.thisdir
            if not tabdir:
                continue
            i = str(i)
            macros[i + 'd'] = tabdir.path
            if tabdir.get_selection():
                macros[i + 'p'] = [os.path.join(tabdir.path, fl.relative_path)
                                   for fl in tabdir.get_selection()]
                macros[i + 's'] = [fl.path for fl in tabdir.get_selection()]
            else:
                macros[i + 'p'] = MACRO_FAIL
                macros[i + 's'] = MACRO_FAIL
            if tabdir.pointed_obj:
                macros[i + 'f'] = tabdir.pointed_obj.path
            else:
                macros[i + 'f'] = MACRO_FAIL

        # define D/F/P/S for the next tab
        found_current_tab = False
        next_tab = None
        first_tab = None
        for tabname in self.fm.tabs:
            if not first_tab:
                first_tab = tabname
            if found_current_tab:
                next_tab = self.fm.tabs[tabname]
                break
            if self.fm.current_tab == tabname:
                found_current_tab = True
        if found_current_tab and next_tab is None:
            next_tab = self.fm.tabs[first_tab]
        next_tab_dir = next_tab.thisdir

        if next_tab_dir:
            macros['D'] = str(next_tab_dir.path)
            if next_tab.thisfile:
                macros['F'] = next_tab.thisfile.path
            else:
                macros['F'] = MACRO_FAIL
            if next_tab_dir.get_selection():
                macros['P'] = [os.path.join(next_tab.path, fl.path)
                               for fl in next_tab.get_selection()]
                macros['S'] = [fl.path for fl in next_tab.get_selection()]
            else:
                macros['P'] = MACRO_FAIL
                macros['S'] = MACRO_FAIL
        else:
            macros['D'] = MACRO_FAIL
            macros['F'] = MACRO_FAIL
            macros['S'] = MACRO_FAIL

        return macros

    def source(self, filename):
        """:source <filename>

        Load a config file.
        """
        filename = os.path.expanduser(filename)
        LOG.debug("Sourcing config file '%s'", filename)
        with open(filename, 'r') as fobj:
            for line in fobj:
                line = line.strip(" \r\n")
                if line.startswith("#") or not line.strip():
                    continue
                try:
                    self.execute_console(line)
                except Exception as ex:  # pylint: disable=broad-except
                    if ranger.args.debug:
                        raise
                    self.notify('Error in line `%s\':\n  %s' % (line, str(ex)), bad=True)

    def execute_file(self, files, **kw):  # pylint: disable=too-many-branches
        """Uses the "rifle" module to open/execute a file

        Arguments are the same as for ranger.ext.rifle.Rifle.execute:

        files: a list of file objects (not strings!)
        number: a number to select which way to open the file, in case there
            are multiple choices
        label: a string to select an opening method by its label
        flags: a string specifying additional options, see `man rifle`
        mimetype: pass the mimetype to rifle, overriding its own guess
        """

        mode = kw['mode'] if 'mode' in kw else 0

        # ranger can act as a file chooser when running with --choosefile=...
        if mode == 0 and 'label' not in kw:
            if ranger.args.choosefile:
                with open(ranger.args.choosefile, 'w') as fobj:
                    fobj.write(self.fm.thisfile.path)

            if ranger.args.choosefiles:
                paths = []
                for hist in self.fm.thistab.history:
                    for fobj in hist.files:
                        if fobj.marked and fobj.path not in paths:
                            paths += [fobj.path]
                paths += [f.path for f in self.fm.thistab.get_selection() if f.path not in paths]

                with open(ranger.args.choosefiles, 'w') as fobj:
                    fobj.write('\n'.join(paths) + '\n')

            if ranger.args.choosefile or ranger.args.choosefiles:
                raise SystemExit

        if isinstance(files, set):
            files = list(files)
        elif not isinstance(files, (list, tuple)):
            files = [files]

        flags = kw.get('flags', '')
        if 'c' in squash_flags(flags):
            files = [self.fm.thisfile]

        self.signal_emit('execute.before', keywords=kw)
        filenames = [f.path for f in files]
        label = kw.get('label', kw.get('app', None))

        def execute():
            return self.rifle.execute(filenames, mode, label, flags, None)
        try:
            return execute()
        except OSError as err:
            # Argument list too long.
            if err.errno == 7 and self.settings.open_all_images:
                old_value = self.settings.open_all_images
                try:
                    self.notify("Too many files: Disabling open_all_images temporarily.")
                    self.settings.open_all_images = False
                    return execute()
                finally:
                    self.settings.open_all_images = old_value
            else:
                raise
        finally:
            self.signal_emit('execute.after')

    # --------------------------
    # -- Moving Around
    # --------------------------

    def move(self,  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
             narg=None, **kw):
        """A universal movement method.

        Accepts these parameters:
        (int) down, (int) up, (int) left, (int) right, (int) to,
        (bool) absolute, (bool) relative, (bool) pages,
        (bool) percentage

        to=X is translated to down=X, absolute=True

        Example:
        self.move(down=4, pages=True)  # moves down by 4 pages.
        self.move(to=2, pages=True)  # moves to page 2.
        self.move(to=80, percentage=True)  # moves to 80%
        """
        cwd = self.thisdir
        kw.setdefault('cycle', self.fm.settings['wrap_scroll'])
        kw.setdefault('one_indexed', self.fm.settings['one_indexed'])
        direction = Direction(kw)
        if 'left' in direction or direction.left() > 0:
            steps = direction.left()
            if narg is not None:
                steps *= narg
            directory = os.path.join(*(['..'] * steps))
            self.thistab.enter_dir(directory)
            self.change_mode('normal')

        if not cwd or not cwd.accessible or not cwd.content_loaded:
            return

        if 'right' in direction:
            mode = 0
            if narg is not None:
                mode = narg
            tfile = self.thisfile
            if kw.get('selection', True):
                selection = self.thistab.get_selection()
            else:
                selection = [tfile]
            if tfile is None:
                return
            if tfile.is_directory:
                self.thistab.enter_dir(tfile)
            elif selection:
                result = self.execute_file(selection, mode=mode)
                if result in (False, ASK_COMMAND):
                    self.open_console('open_with ')
        elif direction.vertical() and cwd.files:
            pos_new = direction.move(
                direction=direction.down(),
                override=narg,
                maximum=len(cwd),
                current=cwd.pointer,
                pagesize=self.ui.browser.hei)
            cwd.move(to=pos_new)
            if self.mode == 'visual':
                pos_start = min(self._visual_pos_start, (len(cwd.files) - 1))
                self._visual_move_cycles += direction.move_cycles()

                # Haven't cycled
                if self._visual_move_cycles == 0:
                    targets = set(cwd.files[min(pos_start, pos_new):(max(pos_start, pos_new) + 1)])
                # Cycled down once
                elif self._visual_move_cycles == 1:
                    if pos_new < pos_start:
                        targets = set(cwd.files[:(pos_new + 1)] + cwd.files[pos_start:])
                    else:
                        targets = set(cwd.files)
                # Cycled up once
                elif self._visual_move_cycles == -1:
                    if pos_new > pos_start:
                        targets = set(cwd.files[:(pos_start + 1)] + cwd.files[pos_new:])
                    else:
                        targets = set(cwd.files)
                # Cycled more than once
                else:
                    targets = set(cwd.files)

                # The current selection
                current = set(cwd.marked_items)
                # Set theory anyone?
                if self._visual_reverse:
                    for fobj in targets & current:
                        cwd.mark_item(fobj, False)
                    for fobj in self._previous_selection - current - targets:
                        cwd.mark_item(fobj, True)
                else:
                    for fobj in targets - current:
                        cwd.mark_item(fobj, True)
                    for fobj in current - self._previous_selection - targets:
                        cwd.mark_item(fobj, False)
            if self.ui.pager.visible:
                self.display_file()

    def move_parent(self, n, narg=None):
        self.change_mode('normal')
        if narg is not None:
            n *= narg
        parent = self.thistab.at_level(-1)
        if parent is not None:
            if parent.pointer + n < 0:
                n = 0 - parent.pointer
            try:
                self.thistab.enter_dir(parent.files[parent.pointer + n])
            except IndexError:
                pass

    def select_file(self, path):
        path = path.strip()
        if self.enter_dir(os.path.dirname(path)):
            self.thisdir.move_to_obj(path)

    def history_go(self, relative):
        """Move back and forth in the history"""
        self.thistab.history_go(int(relative))

    # TODO: remove this method since it is not used?
    def scroll(self, relative):
        """Scroll down by <relative> lines"""
        if self.ui.browser and self.ui.browser.main_column:
            self.ui.browser.main_column.scroll(relative)
            self.thisfile = self.thisdir.pointed_obj

    def enter_dir(self, path, remember=False, history=True):
        """Enter the directory at the given path"""
        cwd = self.thisdir
        # csh variable is lowercase
        cdpath = os.environ.get('CDPATH', None) or os.environ.get('cdpath', None)
        result = self.thistab.enter_dir(path, history=history)
        if result is False and cdpath:
            for comp in cdpath.split(':'):
                curpath = os.path.join(comp, path)
                if os.path.isdir(curpath):
                    result = self.thistab.enter_dir(curpath, history=history)
                    break
        if cwd != self.thisdir:
            if remember:
                self.bookmarks.remember(cwd)
            self.change_mode('normal')
        return result

    def cd(self, path, remember=True):  # pylint: disable=invalid-name
        """enter the directory at the given path, remember=True"""
        self.enter_dir(path, remember=remember)

    def traverse(self):
        self.change_mode('normal')
        tfile = self.thisfile
        cwd = self.thisdir
        if tfile is not None and tfile.is_directory:
            self.enter_dir(tfile.path)
        elif cwd.pointer >= len(cwd) - 1:
            while True:
                self.move(left=1)
                cwd = self.thisdir
                if cwd.pointer < len(cwd) - 1:
                    break
                if cwd.path == '/':
                    break
            self.move(down=1)
            self.traverse()
        else:
            self.move(down=1)
            self.traverse()

    def traverse_backwards(self):
        self.change_mode('normal')
        if self.thisdir.pointer == 0:
            self.move(left=1)
            if self.thisdir.pointer != 0:
                self.traverse_backwards()
        else:
            self.move(up=1)
            while True:
                if self.thisfile is not None and self.thisfile.is_directory:
                    self.enter_dir(self.thisfile.path)
                    self.move(to=100, percentage=True)
                elif self.thisdir.pointer == 0:
                    break
                else:
                    self.move(up=1)

    # --------------------------
    # -- Shortcuts / Wrappers
    # --------------------------

    def pager_move(self, narg=None, **kw):
        self.ui.get_pager().move(narg=narg, **kw)

    def taskview_move(self, narg=None, **kw):
        self.ui.taskview.move(narg=narg, **kw)

    def pause_tasks(self):
        self.loader.pause(-1)

    def pager_close(self):
        if self.ui.pager.visible:
            self.ui.close_pager()
        if self.ui.browser.pager and self.ui.browser.pager.visible:
            self.ui.close_embedded_pager()

    def taskview_open(self):
        self.ui.open_taskview()

    def taskview_close(self):
        self.ui.close_taskview()

    def execute_command(self, cmd, **kw):
        return self.run(cmd, **kw)

    def edit_file(self, file=None):  # pylint: disable=redefined-builtin
        """Calls execute_file with the current file and label='editor'"""
        if file is None:
            file = self.thisfile
        elif isinstance(file, str):
            file = File(os.path.expanduser(file))
        if file is None:
            return
        self.execute_file(file, label='editor')

    def toggle_option(self, string):  # pylint: disable=redefined-outer-name
        """:toggle_option <string>

        Toggle a boolean option named <string>.
        """
        if isinstance(self.settings[string], bool):
            self.settings[string] ^= True
        elif string in ALLOWED_VALUES:
            current = self.settings[string]
            allowed = ALLOWED_VALUES[string]
            if allowed:
                if current not in allowed and current == "":
                    current = allowed[0]
                if current in allowed:
                    self.settings[string] = \
                        allowed[(allowed.index(current) + 1) % len(allowed)]
                else:
                    self.settings[string] = allowed[0]

    def set_option(self, optname, value):
        """:set_option <optname>

        Set the value of an option named <optname>.
        """
        self.settings[optname] = value

    def sort(self, func=None, reverse=None):
        if reverse is not None:
            self.settings['sort_reverse'] = bool(reverse)

        if func is not None:
            self.settings['sort'] = str(func)

    def mark_files(self, all=False,  # pylint: disable=redefined-builtin,too-many-arguments
                   toggle=False, val=None, movedown=None, narg=None):
        """A wrapper for the directory.mark_xyz functions.

        Arguments:
        all - change all files of the current directory at once?
        toggle - toggle the marked-status?
        val - mark or unmark?
        """

        if self.thisdir is None:
            return

        cwd = self.thisdir

        if not cwd.accessible:
            return

        if movedown is None:
            movedown = not all

        if val is None and toggle is False:
            return

        if narg is None:
            narg = 1
        else:
            all = False

        if all:
            if toggle:
                cwd.toggle_all_marks()
            else:
                cwd.mark_all(val)
            if self.mode == 'visual':
                self.change_mode('normal')
        else:
            for i in range(cwd.pointer, min(cwd.pointer + narg, len(cwd))):
                item = cwd.files[i]
                if item is not None:
                    if toggle:
                        cwd.toggle_mark(item)
                    else:
                        cwd.mark_item(item, val)

        if movedown:
            self.move(down=narg)

        self.ui.redraw_main_column()
        self.ui.status.need_redraw = True

    def mark_in_direction(self, val=True, dirarg=None):
        cwd = self.thisdir
        direction = Direction(dirarg)
        pos, selected = direction.select(lst=cwd.files, current=cwd.pointer,
                                         pagesize=self.ui.termsize[0])
        cwd.pointer = pos
        cwd.correct_pointer()
        for item in selected:
            cwd.mark_item(item, val)

    # --------------------------
    # -- Searching
    # --------------------------

    # TODO: Do we still use this method? Should we remove it?
    def search_file(self, text, offset=1, regexp=True):
        if isinstance(text, str) and regexp:
            try:
                text = re.compile(text, re.UNICODE | re.IGNORECASE)  # pylint: disable=no-member
            except re.error:
                return False
        self.thistab.last_search = text
        self.search_next(order='search', offset=offset)
        return None

    def search_next(self, order=None, offset=1, forward=True):
        original_order = order

        if order is None:
            order = self.search_method
        else:
            self.set_search_method(order=order)

        if order in ('search', 'tag'):
            if order == 'search':
                arg = self.thistab.last_search
                if arg is None:
                    return False
                if hasattr(arg, 'search'):
                    def fnc(obj):
                        return arg.search(obj.basename)
                else:
                    def fnc(obj):
                        return arg in obj.basename
            elif order == 'tag':
                def fnc(obj):
                    return obj.realpath in self.tags

            return self.thisdir.search_fnc(fnc=fnc, offset=offset, forward=forward)

        elif order in ('size', 'mimetype', 'ctime', 'mtime', 'atime'):
            cwd = self.thisdir
            if original_order is not None or not cwd.cycle_list:
                lst = list(cwd.files)
                if order == 'size':
                    def fnc(item):
                        return -item.size
                elif order == 'mimetype':
                    def fnc(item):
                        return item.mimetype or ''
                elif order == 'ctime':
                    def fnc(item):
                        return -int(item.stat and item.stat.st_ctime)
                elif order == 'atime':
                    def fnc(item):
                        return -int(item.stat and item.stat.st_atime)
                elif order == 'mtime':
                    def fnc(item):
                        return -int(item.stat and item.stat.st_mtime)
                lst.sort(key=fnc)
                cwd.set_cycle_list(lst)
                return cwd.cycle(forward=None)

            return cwd.cycle(forward=forward)
        return None

    def set_search_method(self, order, forward=True):  # pylint: disable=unused-argument
        if order in ('search', 'tag', 'size', 'mimetype', 'ctime', 'mtime', 'atime'):
            self.search_method = order

    # --------------------------
    # -- Tags
    # --------------------------
    # Tags are saved in ~/.config/ranger/tagged and simply mark if a
    # file is important to you in any context.

    def tag_toggle(self, tag=None, paths=None, value=None, movedown=None):
        """:tag_toggle <character>

        Toggle a tag <character>.

        Keyword arguments:
            tag=<character>
            paths=<paths to tag>
            value=<True: add/False: remove/anything else: toggle>
            movedown=<boolean>
        """
        if not self.tags:
            return
        if paths is None:
            tags = tuple(x.realpath for x in self.thistab.get_selection())
        else:
            tags = [realpath(path) for path in paths]
        if value is True:
            self.tags.add(*tags, tag=tag or self.tags.default_tag)
        elif value is False:
            self.tags.remove(*tags)
        else:
            self.tags.toggle(*tags, tag=tag or self.tags.default_tag)

        if movedown is None:
            movedown = len(tags) == 1 and paths is None
        if movedown:
            self.move(down=1)

        self.ui.redraw_main_column()

    def tag_remove(self, tag=None, paths=None, movedown=None):
        """:tag_remove <character>

        Remove a tag <character>. See :tag_toggle for keyword arguments.
        """
        self.tag_toggle(tag=tag, paths=paths, value=False, movedown=movedown)

    def tag_add(self, tag=None, paths=None, movedown=None):
        """:tag_add <character>

        Add a tag <character>. See :tag_toggle for keyword arguments.
        """
        self.tag_toggle(tag=tag, paths=paths, value=True, movedown=movedown)

    # --------------------------
    # -- Bookmarks
    # --------------------------
    # Using ranger.container.bookmarks.

    def enter_bookmark(self, key):
        """Enter the bookmark with the name <key>"""
        try:
            self.bookmarks.update_if_outdated()
            destination = self.bookmarks[str(key)]
            cwd = self.thisdir
            if destination.path != cwd.path:
                self.bookmarks.enter(str(key))
                self.bookmarks.remember(cwd)
        except KeyError:
            pass

    def set_bookmark(self, key, val=None):
        """Set the bookmark with the name <key> to the current directory"""
        if val is None:
            val = self.thisdir
        else:
            val = Directory(val)
        self.bookmarks.update_if_outdated()
        self.bookmarks[str(key)] = val

    def unset_bookmark(self, key):
        """Delete the bookmark with the name <key>"""
        self.bookmarks.update_if_outdated()
        del self.bookmarks[str(key)]

    def draw_bookmarks(self):
        self.ui.browser.draw_bookmarks = True

    def hide_bookmarks(self):
        self.ui.browser.draw_bookmarks = False

    def draw_possible_programs(self):
        try:
            target = self.thistab.get_selection()[0]
        except IndexError:
            self.ui.browser.draw_info = []
            return
        programs = [program for program in self.rifle.list_commands([target.path], None,
                                                                    skip_ask=True)]
        if programs:
            num_digits = max((len(str(program[0])) for program in programs))
            program_info = ['%s | %s' % (str(program[0]).rjust(num_digits), program[1])
                            for program in programs]
            self.ui.browser.draw_info = program_info

    def hide_console_info(self):
        self.ui.browser.draw_info = False

    # --------------------------
    # -- Pager
    # --------------------------
    # These commands open the built-in pager and set specific sources.

    def display_command_help(self, console_widget):
        try:
            command = console_widget.get_cmd_class()
        except KeyError:
            self.notify("Feature not available!", bad=True)
            return

        if not command:
            self.notify("Command not found!", bad=True)
            return

        if not command.__doc__:
            self.notify("Command has no docstring. Try using python without -OO", bad=True)
            return

        pager = self.ui.open_pager()
        lines = cleandoc(command.__doc__).split('\n')
        pager.set_source(lines)

    def display_help(self):
        manualpath = self.relpath('../doc/ranger.1')
        if os.path.exists(manualpath):
            process = self.run(['man', manualpath])
            if process.poll() != 16:
                return
        process = self.run(['man', 'ranger'])
        if process.poll() == 16:
            self.notify("Could not find manpage.", bad=True)

    def display_log(self):
        logs = list(self.get_log())
        pager = self.ui.open_pager()
        if logs:
            pager.set_source(["Message Log:"] + logs)
        else:
            pager.set_source(["Message Log:", "No messages!"])
        pager.move(to=100, percentage=True)

    def display_file(self):
        if not self.thisfile or not self.thisfile.is_file:
            return

        pager = self.ui.open_pager()
        fobj = self.thisfile.get_preview_source(pager.wid, pager.hei)
        if self.thisfile.is_image_preview():
            pager.set_image(fobj)
        else:
            pager.set_source(fobj)

    def scroll_preview(self, lines, narg=None):
        """:scroll_preview <lines>

        Scroll the file preview by <lines> lines.
        """
        preview_column = self.ui.browser.columns[-1]
        if preview_column.target and preview_column.target.is_file:
            if narg is not None:
                lines = narg
            preview_column.scrollbit(lines)

    # --------------------------
    # -- Previews
    # --------------------------
    def update_preview(self, path):
        try:
            del self.previews[path]
        except KeyError:
            return False
        self.ui.need_redraw = True
        return True

    @staticmethod
    def sha1_encode(path):
        if version_info[0] < 3:
            return os.path.join(ranger.args.cachedir, sha1(path).hexdigest()) + '.jpg'
        return os.path.join(ranger.args.cachedir,
                            sha1(path.encode('utf-8', 'backslashreplace')).hexdigest()) + '.jpg'

    def get_preview(self, fobj, width, height):  # pylint: disable=too-many-return-statements
        pager = self.ui.get_pager()
        path = fobj.realpath

        if not path or not os.path.exists(path):
            return None

        if not self.settings.preview_script or not self.settings.use_preview_script:
            try:
                # XXX: properly determine file's encoding
                return codecs.open(path, 'r', errors='ignore')
            # IOError for Python2, OSError for Python3
            except (IOError, OSError):
                return None

        # self.previews is a 2 dimensional dict:
        # self.previews['/tmp/foo.jpg'][(80, 24)] = "the content..."
        # self.previews['/tmp/foo.jpg']['loading'] = False
        # A -1 in tuples means "any"; (80, -1) = wid. of 80 and any hei.
        # The key 'foundpreview' is added later. Values in (True, False)
        # XXX: Previews can break when collapse_preview is on and the
        # preview column is popping out as you move the cursor on e.g. a
        # PDF file.
        try:
            data = self.previews[path]
        except KeyError:
            data = self.previews[path] = {'loading': False}
        else:
            if data['loading']:
                return None

        found = data.get(
            (-1, -1), data.get(
                (width, -1), data.get(
                    (-1, height), data.get(
                        (width, height), False
                    )
                )
            )
        )
        if found is not False:
            return found

        try:
            stat_ = os.stat(self.settings.preview_script)
        except OSError:
            self.fm.notify("Preview script `{0}` doesn't exist!".format(
                self.settings.preview_script), bad=True)
            return None

        if not stat_.st_mode & S_IEXEC:
            self.fm.notify("Preview script `{0}` is not executable!".format(
                self.settings.preview_script), bad=True)
            return None

        data['loading'] = True

        if 'directimagepreview' in data:
            data['foundpreview'] = True
            data['imagepreview'] = True
            pager.set_image(path)
            data['loading'] = False
            return path

        if ranger.args.clean:
            # Don't access args.cachedir in clean mode
            return None

        if not os.path.exists(ranger.args.cachedir):
            os.makedirs(ranger.args.cachedir)
        cacheimg = os.path.join(ranger.args.cachedir, self.sha1_encode(path))
        if self.settings.preview_images and \
                os.path.isfile(cacheimg) and \
                os.path.getmtime(cacheimg) > os.path.getmtime(path):
            data['foundpreview'] = True
            data['imagepreview'] = True
            pager.set_image(cacheimg)
            data['loading'] = False
            return cacheimg

        def on_after(signal):
            rcode = signal.process.poll()
            content = signal.loader.stdout_buffer
            data['foundpreview'] = True

            if rcode == 0:
                data[(width, height)] = content
            elif rcode == 3:
                data[(-1, height)] = content
            elif rcode == 4:
                data[(width, -1)] = content
            elif rcode == 5:
                data[(-1, -1)] = content
            elif rcode == 6:
                data['imagepreview'] = True
            elif rcode == 7:
                data['directimagepreview'] = True
            elif rcode == 1:
                data[(-1, -1)] = None
                data['foundpreview'] = False
            elif rcode == 2:
                text = self.read_text_file(path, 1024 * 32)
                if not isinstance(text, str):
                    # Convert 'unicode' to 'str' in Python 2
                    text = text.encode('utf-8')
                data[(-1, -1)] = text
            else:
                data[(-1, -1)] = None

            if self.thisfile and self.thisfile.realpath == path:
                self.ui.browser.need_redraw = True

            data['loading'] = False

            pager = self.ui.get_pager()
            if self.thisfile and self.thisfile.is_file:
                if 'imagepreview' in data:
                    pager.set_image(cacheimg)
                    return cacheimg
                elif 'directimagepreview' in data:
                    pager.set_image(path)
                    return path
                else:
                    pager.set_source(self.thisfile.get_preview_source(
                        pager.wid, pager.hei))
            return None

        def on_destroy(signal):  # pylint: disable=unused-argument
            try:
                del self.previews[path]
            except KeyError:
                pass

        loadable = CommandLoader(
            args=[self.settings.preview_script, path, str(width), str(height),
                  cacheimg, str(self.settings.preview_images)],
            read=True,
            silent=True,
            descr="Getting preview of %s" % path,
        )
        loadable.signal_bind('after', on_after)
        loadable.signal_bind('destroy', on_destroy)
        self.loader.add(loadable)

        return None

    @staticmethod
    def read_text_file(path, count=None):
        """Encoding-aware reading of a text file."""
        # Guess encoding ourselves.
        # These should be the most frequently used ones.
        # latin-1 as the last resort
        encodings = [('utf-8', 'strict'), ('utf-16', 'strict'),
                     ('latin-1', 'replace')]

        with open(path, 'rb') as fobj:
            data = fobj.read(count)

        try:
            import chardet
        except ImportError:
            pass
        else:
            result = chardet.detect(data)
            guessed_encoding = result['encoding']
            if guessed_encoding is not None:
                # Add chardet's guess before our own.
                encodings.insert(0, (guessed_encoding, 'replace'))

        for (encoding, error_scheme) in encodings:
            try:
                text = codecs.decode(data, encoding, error_scheme)
            except UnicodeDecodeError:
                pass
            else:
                LOG.debug("Guessed encoding of '%s' as %s", path, encoding)
                return text

    # --------------------------
    # -- Tabs
    # --------------------------
    def tab_open(self, name, path=None):
        tab_has_changed = (name != self.current_tab)
        self.current_tab = name
        previous_tab = self.thistab
        try:
            tab = self.tabs[name]
        except KeyError:
            # create a new tab
            tab = Tab(self.thistab.path)
            self.tabs[name] = tab
            self.thistab = tab
            tab.enter_dir(tab.path, history=False)
            if path:
                tab.enter_dir(path, history=True)
            if previous_tab:
                tab.inherit_history(previous_tab.history)
        else:
            self.thistab = tab
            if path:
                tab.enter_dir(path, history=True)
            else:
                tab.enter_dir(tab.path, history=False)

        if tab_has_changed:
            self.change_mode('normal')
            self.signal_emit('tab.change', old=previous_tab, new=self.thistab)
            self.signal_emit('tab.layoutchange')

    def tab_close(self, name=None):
        if name is None:
            name = self.current_tab
        tab = self.tabs[name]
        if name == self.current_tab:
            direction = -1 if name == self.get_tab_list()[-1] else 1
            previous = self.current_tab
            self.tab_move(direction)
            if previous == self.current_tab:
                return  # can't close last tab
        if name in self.tabs:
            del self.tabs[name]
        self.restorable_tabs.append(tab)
        self.signal_emit('tab.layoutchange')

    def tab_restore(self):
        # NOTE: The name of the tab is not restored.
        previous_tab = self.thistab
        if self.restorable_tabs:
            tab = self.restorable_tabs.pop()
            for name in range(1, len(self.tabs) + 2):
                if name not in self.tabs:
                    self.current_tab = name
                    self.tabs[name] = tab
                    tab.enter_dir(tab.path, history=False)
                    self.thistab = tab
                    self.change_mode('normal')
                    self.signal_emit('tab.change', old=previous_tab, new=self.thistab)
                    break

    def tab_move(self, offset, narg=None):
        if narg:
            return self.tab_open(narg)
        assert isinstance(offset, int)
        tablist = self.get_tab_list()
        current_index = tablist.index(self.current_tab)
        newtab = tablist[(current_index + offset) % len(tablist)]
        if newtab != self.current_tab:
            self.tab_open(newtab)
        return None

    def tab_new(self, path=None, narg=None):
        if narg:
            return self.tab_open(narg, path)
        i = 1
        while i in self.tabs:
            i += 1
        return self.tab_open(i, path)

    def tab_shift(self, offset=0, to=None):  # pylint: disable=invalid-name
        """Shift the tab left/right

        Shift the current tab to the left or right by either:
        offset - changes the tab number by offset
        to - shifts the tab to the specified tab number
        """

        oldtab_index = self.current_tab
        if to is None:
            assert isinstance(offset, int)
            # enumerated index (1 to 9)
            newtab_index = oldtab_index + offset
        else:
            assert isinstance(to, int)
            newtab_index = to
        # shift tabs without enumerating, preserve tab numbers when can
        if newtab_index != oldtab_index:
            # the other tabs shift in the opposite direction
            if (newtab_index - oldtab_index) > 0:
                direction = -1
            else:
                direction = 1

            def tabshiftreorder(source_index):
                # shift the tabs to make source_index empty
                if source_index in self.tabs:
                    target_index = source_index + direction
                    # make the target_index empty recursively
                    tabshiftreorder(target_index)
                    # shift the source to target
                    source_tab = self.tabs[source_index]
                    self.tabs[target_index] = source_tab
                    del self.tabs[source_index]

            # first remove the current tab from the dict
            oldtab = self.tabs[oldtab_index]
            del self.tabs[oldtab_index]
            # make newtab_index empty by shifting
            tabshiftreorder(newtab_index)
            self.tabs[newtab_index] = oldtab
            self.current_tab = newtab_index
            self.thistab = oldtab
            self.ui.titlebar.request_redraw()
            self.signal_emit('tab.layoutchange')
        return None

    def tab_switch(self, path, create_directory=False):
        """Switches to tab of given path, opening a new tab as necessary.

        If path does not exist, it is treated as a directory.
        """
        path = realpath(path)
        if not os.path.exists(path):
            file_selection = None
            if create_directory:
                try:
                    if not os.path.isdir(path):
                        os.makedirs(path)
                except OSError as err:
                    self.fm.notify(err, bad=True)
                    return
                target_directory = path
            else:
                # Give benefit of the doubt.
                potential_parent = os.path.dirname(path)
                if os.path.exists(potential_parent) and os.path.isdir(potential_parent):
                    target_directory = potential_parent
                else:
                    self.fm.notify("Unable to resolve given path.", bad=True)
                    return
        elif os.path.isdir(path):
            file_selection = None
            target_directory = path
        else:
            file_selection = path
            target_directory = os.path.dirname(path)

        for name in self.fm.tabs:
            tab = self.fm.tabs[name]
            # Is a tab already open?
            if tab.path == target_directory:
                self.fm.tab_open(name=name)
                if file_selection:
                    self.fm.select_file(file_selection)
                return

        self.fm.tab_new(path=target_directory)
        if file_selection:
            self.fm.select_file(file_selection)

    def get_tab_list(self):
        assert self.tabs, "There must be at least 1 tab at all times"

        class NaturalOrder(object):  # pylint: disable=too-few-public-methods
            def __init__(self, obj):
                self.obj = obj

            def __lt__(self, other):
                try:
                    return self.obj < other.obj
                except TypeError:
                    return str(self.obj) < str(other.obj)

        return sorted(self.tabs, key=NaturalOrder)

    # --------------------------
    # -- Overview of internals
    # --------------------------

    def _run_pager(self, path):
        self.run(shlex.split(os.environ.get('PAGER', ranger.DEFAULT_PAGER)) + [path])

    def dump_keybindings(self, *contexts):
        if not contexts:
            contexts = 'browser', 'console', 'pager', 'taskview'

        temporary_file = tempfile.NamedTemporaryFile()

        def write(string):  # pylint: disable=redefined-outer-name
            temporary_file.write(string.encode('utf-8'))

        def recurse(before, pointer):
            for key, value in pointer.items():
                keys = before + [key]
                if isinstance(value, dict):
                    recurse(keys, value)
                else:
                    write("%12s %s\n" % (construct_keybinding(keys), value))

        for context in contexts:
            write("Keybindings in `%s'\n" % context)
            if context in self.fm.ui.keymaps:
                recurse([], self.fm.ui.keymaps[context])
            else:
                write("  None\n")
            write("\n")

        temporary_file.flush()
        self._run_pager(temporary_file.name)

    def dump_commands(self):
        temporary_file = tempfile.NamedTemporaryFile()

        def write(string):  # pylint: disable=redefined-outer-name
            temporary_file.write(string.encode('utf-8'))

        undocumented = []
        for cmd_name in sorted(self.commands.commands):
            cmd = self.commands.commands[cmd_name]
            if hasattr(cmd, '__doc__') and cmd.__doc__:
                doc = cleandoc(cmd.__doc__)
                if doc[0] == ':':
                    write(doc)
                    write("\n\n" + "-" * 60 + "\n")
            else:
                undocumented.append(cmd)

        if undocumented:
            write("Undocumented commands:\n\n")
            for cmd in undocumented:
                write("    :%s\n" % cmd.get_name())

        temporary_file.flush()
        self._run_pager(temporary_file.name)

    def dump_settings(self):
        temporary_file = tempfile.NamedTemporaryFile()

        def write(string):  # pylint: disable=redefined-outer-name
            temporary_file.write(string.encode('utf-8'))

        for setting in sorted(ALLOWED_SETTINGS):
            write("%30s = %s\n" % (setting, getattr(self.settings, setting)))

        temporary_file.flush()
        self._run_pager(temporary_file.name)

    # --------------------------
    # -- File System Operations
    # --------------------------

    def uncut(self):
        """:uncut

        Empty the copy buffer.
        """
        self.copy_buffer = set()
        self.do_cut = False
        self.ui.browser.main_column.request_redraw()

    def copy(self, mode='set', narg=None, dirarg=None):
        """:copy [mode=set]

        Copy the selected items.
        Modes are: 'set', 'add', 'remove'.
        """
        assert mode in ('set', 'add', 'remove', 'toggle')
        cwd = self.thisdir
        if not narg and not dirarg:
            selected = (fobj for fobj in self.thistab.get_selection() if fobj in cwd.files)
        else:
            if not dirarg and narg:
                direction = Direction(down=1)
                offset = 0
            else:
                direction = Direction(dirarg)
                offset = 1
            pos, selected = direction.select(override=narg, lst=cwd.files, current=cwd.pointer,
                                             pagesize=self.ui.termsize[0], offset=offset)
            cwd.pointer = pos
            cwd.correct_pointer()
        if mode == 'set':
            self.copy_buffer = set(selected)
        elif mode == 'add':
            self.copy_buffer.update(set(selected))
        elif mode == 'remove':
            self.copy_buffer.difference_update(set(selected))
        elif mode == 'toggle':
            self.copy_buffer.symmetric_difference_update(set(selected))
        self.do_cut = False
        self.ui.browser.main_column.request_redraw()

    def cut(self, mode='set', narg=None, dirarg=None):
        """:cut [mode=set]

        Cut the selected items.
        Modes are: 'set, 'add, 'remove.
        """
        self.copy(mode=mode, narg=narg, dirarg=dirarg)
        self.do_cut = True
        self.ui.browser.main_column.request_redraw()

    def paste_symlink(self, relative=False):
        copied_files = self.copy_buffer
        for fobj in copied_files:
            new_name = next_available_filename(fobj.basename)
            self.notify(new_name)
            try:
                if relative:
                    relative_symlink(fobj.path, join(self.fm.thisdir.path, new_name))
                else:
                    symlink(fobj.path, join(self.fm.thisdir.path, new_name))
            except OSError as ex:
                self.notify('Failed to paste symlink: View log for more info',
                            bad=True, exception=ex)

    def paste_hardlink(self):
        for fobj in self.copy_buffer:
            new_name = next_available_filename(fobj.basename)
            try:
                link(fobj.path, join(self.fm.thisdir.path, new_name))
            except OSError as ex:
                self.notify('Failed to paste hardlink: View log for more info',
                            bad=True, exception=ex)

    def paste_hardlinked_subtree(self):
        for fobj in self.copy_buffer:
            try:
                target_path = join(self.fm.thisdir.path, fobj.basename)
                self._recurse_hardlinked_tree(fobj.path, target_path)
            except OSError as ex:
                self.notify('Failed to paste hardlinked subtree: View log for more info',
                            bad=True, exception=ex)

    def _recurse_hardlinked_tree(self, source_path, target_path):
        if isdir(source_path):
            if not exists(target_path):
                os.mkdir(target_path, stat(source_path).st_mode)
            for item in listdir(source_path):
                self._recurse_hardlinked_tree(
                    join(source_path, item),
                    join(target_path, item))
        else:
            if not exists(target_path) \
                    or stat(source_path).st_ino != stat(target_path).st_ino:
                link(source_path,
                     next_available_filename(target_path))

    def paste(self, overwrite=False, append=False, dest=None):
        """:paste

        Paste the selected items into the current directory or to dest
        if provided.
        """
        if dest is None or isdir(dest):
            loadable = CopyLoader(self.copy_buffer, self.do_cut, overwrite,
                                  dest)
            self.loader.add(loadable, append=append)
            self.do_cut = False
        else:
            self.notify('Failed to paste. The given path is invalid.', bad=True)

    def delete(self, files=None):
        # XXX: warn when deleting mount points/unseen marked files?
        self.notify("Deleting!")
        # COMPAT: old command.py use fm.delete() without arguments
        if files is None:
            files = (fobj.path for fobj in self.thistab.get_selection())
        files = [os.path.abspath(path) for path in files]
        for path in files:
            # Untag the deleted files.
            for tag in self.fm.tags.tags:
                if str(tag).startswith(path):
                    self.fm.tags.remove(tag)
        self.copy_buffer = set(fobj for fobj in self.copy_buffer if fobj.path not in files)
        for path in files:
            if isdir(path) and not os.path.islink(path):
                try:
                    shutil.rmtree(path)
                except OSError as err:
                    self.notify(err)
            else:
                try:
                    os.remove(path)
                except OSError as err:
                    self.notify(err)
        self.thistab.ensure_correct_pointer()

    def mkdir(self, name):
        try:
            os.makedirs(os.path.join(self.thisdir.path, name))
        except OSError as err:
            self.notify(err)

    def rename(self, src, dest):
        if hasattr(src, 'path'):
            src = src.path

        try:
            os.makedirs(os.path.dirname(dest))
        except OSError:
            pass
        try:
            os.rename(src, dest)
        except OSError as err:
            self.notify(err)
            return False
        return True
