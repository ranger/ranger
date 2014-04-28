# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lepus.uberspace.de>
# This software is distributed under the terms of the GNU GPL version 3.

import codecs
import os
import re
import shutil
import string
import tempfile
from os.path import join, isdir, realpath, exists
from os import link, symlink, getcwd, listdir, stat
from inspect import cleandoc
from stat import S_IEXEC
from hashlib import sha1
from sys import version_info

import ranger
from ranger.ext.direction import Direction
from ranger.ext.relative_symlink import relative_symlink
from ranger.ext.keybinding_parser import key_to_string, construct_keybinding
from ranger.ext.shell_escape import shell_quote
from ranger.ext.next_available_filename import next_available_filename
from ranger.ext.rifle import squash_flags, ASK_COMMAND
from ranger.core.shared import FileManagerAware, EnvironmentAware, \
        SettingsAware
from ranger.core.tab import Tab
from ranger.container.file import File
from ranger.core.loader import CommandLoader, CopyLoader
from ranger.container.settings import ALLOWED_SETTINGS

MACRO_FAIL = "<\x01\x01MACRO_HAS_NO_VALUE\x01\01>"

class _MacroTemplate(string.Template):
    """A template for substituting macros in commands"""
    delimiter = ranger.MACRO_DELIMITER

class Actions(FileManagerAware, EnvironmentAware, SettingsAware):
    # --------------------------
    # -- Basic Commands
    # --------------------------

    def exit(self):
        """Exit the program"""
        raise SystemExit()

    def reset(self):
        """Reset the filemanager, clearing the directory buffer"""
        old_path = self.thisdir.path
        self.previews = {}
        self.garbage_collect(-1)
        self.enter_dir(old_path)
        self.change_mode('normal')

    def change_mode(self, mode):
        if mode == self.mode:
            return
        if mode == 'visual':
            self._visual_start       = self.thisdir.pointed_obj
            self._visual_start_pos   = self.thisdir.pointer
            self._previous_selection = set(self.thisdir.marked_items)
            self.mark_files(val=not self._visual_reverse, movedown=False)
        elif mode == 'normal':
            if self.mode == 'visual':
                self._visual_start       = None
                self._visual_start_pos   = None
                self._previous_selection = None
        else:
            return
        self.mode = mode
        self.ui.status.request_redraw()

    def set_option_from_string(self, option_name, value, localpath=None, tags=None):
        if option_name not in ALLOWED_SETTINGS:
            raise ValueError("The option named `%s' does not exist" %
                    option_name)
        if not isinstance(value, str):
            raise ValueError("The value for an option needs to be a string.")

        self.settings.set(option_name, self._parse_option_value(option_name, value), localpath, tags)


    def _parse_option_value(self, name, value):
        types = self.fm.settings.types_of(name)
        if bool in types:
            if value.lower() in ('false', 'off', '0'):
                return False
            elif value.lower() in ('true', 'on', '1'):
                return True
        if type(None) in types and value.lower() == 'none':
            return None
        if int in types:
            try:
                return int(value)
            except ValueError:
                pass
        if str in types:
            return value
        if list in types:
            return value.split(',')
        raise ValueError("Invalid value `%s' for option `%s'!" % (name, value))

    def toggle_visual_mode(self, reverse=False, narg=None):
        if self.mode == 'normal':
            self._visual_reverse = reverse
            if narg != None:
                self.mark_files(val=not reverse, narg=narg)
            self.change_mode('visual')
        else:
            self.change_mode('normal')

    def reload_cwd(self):
        try:
            cwd = self.thisdir
        except:
            pass
        cwd.unload()
        cwd.load_content()

    def notify(self, text, duration=4, bad=False):
        if isinstance(text, Exception):
            if ranger.arg.debug:
                raise
            bad = True
        elif bad == True and ranger.arg.debug:
            raise Exception(str(text))
        text = str(text)
        self.log.appendleft(text)
        if self.ui and self.ui.is_on:
            self.ui.status.notify("  ".join(text.split("\n")),
                    duration=duration, bad=bad)
        else:
            print(text)

    def abort(self):
        try:
            item = self.loader.queue[0]
        except:
            self.notify("Type Q or :quit<Enter> to exit ranger")
        else:
            self.notify("Aborting: " + item.get_description())
            self.loader.remove(index=0)

    def get_cumulative_size(self):
        for f in self.thistab.get_selection() or ():
            f.look_up_cumulative_size()
        self.ui.status.request_redraw()
        self.ui.redraw_main_column()

    def redraw_window(self):
        """Redraw the window"""
        self.ui.redraw_window()

    def open_console(self, string='', prompt=None, position=None):
        """Open the console"""
        self.change_mode('normal')
        self.ui.open_console(string, prompt=prompt, position=position)

    def execute_console(self, string='', wildcards=[], quantifier=None):
        """Execute a command for the console"""
        command_name = string.split()[0]
        cmd_class = self.commands.get_command(command_name, abbrev=False)
        if cmd_class is None:
            self.notify("Command not found: `%s'" % command_name, bad=True)
            return
        cmd = cmd_class(string)
        if cmd.resolve_macros and _MacroTemplate.delimiter in string:
            macros = dict(('any%d'%i, key_to_string(char)) \
                    for i, char in enumerate(wildcards))
            if 'any0' in macros:
                macros['any'] = macros['any0']
            try:
                string = self.substitute_macros(string, additional=macros,
                        escape=cmd.escape_macros_for_shell)
            except ValueError as e:
                if ranger.arg.debug:
                    raise
                else:
                    return self.notify(e)
        try:
            cmd_class(string, quantifier=quantifier).execute()
        except Exception as e:
            if ranger.arg.debug:
                raise
            else:
                self.notify(e)

    def substitute_macros(self, string, additional=dict(), escape=False):
        macros = self._get_macros()
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

    def _get_macros(self):
        macros = {}

        macros['rangerdir'] = ranger.RANGERDIR

        if self.fm.thisfile:
            macros['f'] = self.fm.thisfile.basename
        else:
            macros['f'] = MACRO_FAIL

        if self.fm.thistab.get_selection:
            macros['s'] = [fl.basename for fl in self.fm.thistab.get_selection()]
        else:
            macros['s'] = MACRO_FAIL

        if self.fm.copy_buffer:
            macros['c'] = [fl.path for fl in self.fm.copy_buffer]
        else:
            macros['c'] = MACRO_FAIL

        if self.fm.thisdir.files:
            macros['t'] = [fl.basename for fl in self.fm.thisdir.files
                    if fl.realpath in (self.fm.tags or [])]
        else:
            macros['t'] = MACRO_FAIL

        if self.fm.thisdir:
            macros['d'] = self.fm.thisdir.path
        else:
            macros['d'] = '.'

        # define d/f/s macros for each tab
        for i in range(1,10):
            try:
                tab = self.fm.tabs[i]
            except:
                continue
            tabdir = tab.thisdir
            if not tabdir:
                continue
            i = str(i)
            macros[i + 'd'] = tabdir.path
            if tabdir.get_selection():
                macros[i + 's'] = [fl.path for fl in tabdir.get_selection()]
            else:
                macros[i + 's'] = MACRO_FAIL
            if tabdir.pointed_obj:
                macros[i + 'f'] = tabdir.pointed_obj.path
            else:
                macros[i + 'f'] = MACRO_FAIL

        # define D/F/S for the next tab
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
                macros['S'] = [fl.path for fl in next_tab.get_selection()]
            else:
                macros['S'] = MACRO_FAIL
        else:
            macros['D'] = MACRO_FAIL
            macros['F'] = MACRO_FAIL
            macros['S'] = MACRO_FAIL

        return macros

    def source(self, filename):
        filename = os.path.expanduser(filename)
        for line in open(filename, 'r'):
            line = line.lstrip().rstrip("\r\n")
            if line.startswith("#") or not line.strip():
                continue
            try:
                self.execute_console(line)
            except Exception as e:
                if ranger.arg.debug:
                    raise
                else:
                    self.notify('Error in line `%s\':\n  %s' %
                            (line, str(e)), bad=True)

    def execute_file(self, files, **kw):
        """Execute a file.

        app is the name of a method in Applications, without the "app_"
        flags is a string consisting of runner.ALLOWED_FLAGS
        mode is a positive integer.
        Both flags and mode specify how the program is run."""

        mode = kw['mode'] if 'mode' in kw else 0

        # ranger can act as a file chooser when running with --choosefile=...
        if mode == 0 and 'label' not in kw:
            if ranger.arg.choosefile:
                open(ranger.arg.choosefile, 'w').write(self.fm.thisfile.path)

            if ranger.arg.choosefiles:
                open(ranger.arg.choosefiles, 'w').write("".join(
                    f.path + "\n" for f in self.fm.thistab.get_selection()))

            if ranger.arg.choosefile or ranger.arg.choosefiles:
                raise SystemExit()

        if isinstance(files, set):
            files = list(files)
        elif type(files) not in (list, tuple):
            files = [files]

        flags = kw.get('flags', '')
        if 'c' in squash_flags(flags):
            files = [self.fm.thisfile]

        self.signal_emit('execute.before', keywords=kw)
        filenames = [f.path for f in files]
        label = kw.get('label', kw.get('app', None))
        try:
            return self.rifle.execute(filenames, mode, label, flags, None)
        finally:
            self.signal_emit('execute.after')

    # --------------------------
    # -- Moving Around
    # --------------------------

    def move(self, narg=None, **kw):
        """A universal movement method.

        Accepts these parameters:
        (int) down, (int) up, (int) left, (int) right, (int) to,
        (bool) absolute, (bool) relative, (bool) pages,
        (bool) percentage

        to=X is translated to down=X, absolute=True

        Example:
        self.move(down=4, pages=True)  # moves down by 4 pages.
        self.move(to=2, pages=True)  # moves to page 2.
        self.move(to=1, percentage=True)  # moves to 80%
        """
        cwd = self.thisdir
        direction = Direction(kw)
        if 'left' in direction or direction.left() > 0:
            steps = direction.left()
            if narg is not None:
                steps *= narg
            try:
                directory = os.path.join(*(['..'] * steps))
            except:
                return
            self.thistab.enter_dir(directory)
            self.change_mode('normal')
        if cwd and cwd.accessible and cwd.content_loaded:
            if 'right' in direction:
                mode = 0
                if narg is not None:
                    mode = narg
                cf = self.thisfile
                selection = self.thistab.get_selection()
                if not self.thistab.enter_dir(cf) and selection:
                    result = self.execute_file(selection, mode=mode)
                    if result in (False, ASK_COMMAND):
                        self.open_console('open_with ')
            elif direction.vertical() and cwd.files:
                newpos = direction.move(
                        direction=direction.down(),
                        override=narg,
                        maximum=len(cwd),
                        current=cwd.pointer,
                        pagesize=self.ui.browser.hei)
                cwd.move(to=newpos)
                if self.mode == 'visual':
                    try:
                        startpos = cwd.index(self._visual_start)
                    except:
                        self._visual_start = None
                        startpos = min(self._visual_start_pos, len(cwd))
                    # The files between here and _visual_start_pos
                    targets = set(cwd.files[min(startpos, newpos):\
                            max(startpos, newpos) + 1])
                    # The selection before activating visual mode
                    old = self._previous_selection
                    # The current selection
                    current = set(cwd.marked_items)

                    # Set theory anyone?
                    if not self._visual_reverse:
                        for f in targets - current:
                            cwd.mark_item(f, True)
                        for f in current - old - targets:
                            cwd.mark_item(f, False)
                    else:
                        for f in targets & current:
                            cwd.mark_item(f, False)
                        for f in old - current - targets:
                            cwd.mark_item(f, True)
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
                self.thistab.enter_dir(parent.files[parent.pointer+n])
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
        # bash and ksh syntax
        cdpath = os.environ.get('CDPATH', None)
        if cdpath == "":
            # zsh and csh syntax
            os.environ.get('cdpath', None)
        paths = cdpath.split(':')
        result = self.thistab.enter_dir(path, history=history)
        if result == 0:
            for p in paths:
                curpath = p + '/' + path
                if os.path.isdir(curpath):
                    result = self.thistab.enter_dir(curpath, history=history)
                    break
        if cwd != self.thisdir:
            if remember:
                self.bookmarks.remember(cwd)
            self.change_mode('normal')
        return result

    def cd(self, path, remember=True):
        """enter the directory at the given path, remember=True"""
        self.enter_dir(path, remember=remember)

    def traverse(self):
        self.change_mode('normal')
        cf = self.thisfile
        cwd = self.thisdir
        if cf is not None and cf.is_directory:
            self.enter_dir(cf.path)
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
        if self.ui.browser.pager.visible:
            self.ui.close_embedded_pager()

    def taskview_open(self):
        self.ui.open_taskview()

    def taskview_close(self):
        self.ui.close_taskview()

    def execute_command(self, cmd, **kw):
        return self.run(cmd, **kw)

    def edit_file(self, file=None):
        """Calls execute_file with the current file and label='editor'"""
        if file is None:
            file = self.thisfile
        elif isinstance(file, str):
            file = File(os.path.expanduser(file))
        if file is None:
            return
        self.execute_file(file, label='editor')

    def toggle_option(self, string):
        """Toggle a boolean option named <string>"""
        if isinstance(self.settings[string], bool):
            self.settings[string] ^= True

    def set_option(self, optname, value):
        """Set the value of an option named <optname>"""
        self.settings[optname] = value

    def sort(self, func=None, reverse=None):
        if reverse is not None:
            self.settings['sort_reverse'] = bool(reverse)

        if func is not None:
            self.settings['sort'] = str(func)

    def set_filter(self, fltr):
        try:
            self.thisdir.filter = fltr
        except:
            pass

    def mark_files(self, all=False, toggle=False, val=None, movedown=None, narg=None):
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

        if narg == None:
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

    def search_file(self, text, offset=1, regexp=True):
        if isinstance(text, str) and regexp:
            try:
                text = re.compile(text, re.L | re.U | re.I)
            except:
                return False
        self.thistab.last_search = text
        self.search_next(order='search', offset=offset)

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
                    fnc = lambda x: arg.search(x.basename)
                else:
                    fnc = lambda x: arg in x.basename
            elif order == 'tag':
                fnc = lambda x: x.realpath in self.tags

            return self.thisdir.search_fnc(fnc=fnc, offset=offset, forward=forward)

        elif order in ('size', 'mimetype', 'ctime', 'mtime', 'atime'):
            cwd = self.thisdir
            if original_order is not None or not cwd.cycle_list:
                lst = list(cwd.files)
                if order == 'size':
                    fnc = lambda item: -item.size
                elif order == 'mimetype':
                    fnc = lambda item: item.mimetype or ''
                elif order == 'ctime':
                    fnc = lambda item: -int(item.stat and item.stat.st_ctime)
                elif order == 'atime':
                    fnc = lambda item: -int(item.stat and item.stat.st_atime)
                elif order == 'mtime':
                    fnc = lambda item: -int(item.stat and item.stat.st_mtime)
                lst.sort(key=fnc)
                cwd.set_cycle_list(lst)
                return cwd.cycle(forward=None)

            return cwd.cycle(forward=forward)

    def set_search_method(self, order, forward=True):
        if order in ('search', 'tag', 'size', 'mimetype', 'ctime',
                'mtime', 'atime'):
            self.search_method = order

    # --------------------------
    # -- Tags
    # --------------------------
    # Tags are saved in ~/.config/ranger/tagged and simply mark if a
    # file is important to you in any context.

    def tag_toggle(self, paths=None, value=None, movedown=None, tag=None):
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

    def tag_remove(self, paths=None, movedown=None):
        self.tag_toggle(paths=paths, value=False, movedown=movedown)

    def tag_add(self, paths=None, movedown=None):
        self.tag_toggle(paths=paths, value=True, movedown=movedown)

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

    def set_bookmark(self, key):
        """Set the bookmark with the name <key> to the current directory"""
        self.bookmarks.update_if_outdated()
        self.bookmarks[str(key)] = self.thisdir

    def unset_bookmark(self, key):
        """Delete the bookmark with the name <key>"""
        self.bookmarks.update_if_outdated()
        self.bookmarks.delete(str(key))

    def draw_bookmarks(self):
        self.ui.browser.draw_bookmarks = True

    def hide_bookmarks(self):
        self.ui.browser.draw_bookmarks = False

    def draw_possible_programs(self):
        try:
            target = self.thistab.get_selection()[0]
        except:
            self.ui.browser.draw_info = []
            return
        programs = self.rifle.list_commands([target.path], None)
        programs = ['%s | %s' % program[0:2] for program in programs]
        self.ui.browser.draw_info = programs

    def hide_console_info(self):
        self.ui.browser.draw_info = False

    # --------------------------
    # -- Pager
    # --------------------------
    # These commands open the built-in pager and set specific sources.

    def display_command_help(self, console_widget):
        try:
            command = console_widget._get_cmd_class()
        except:
            self.notify("Feature not available!", bad=True)
            return

        if not command:
            self.notify("Command not found!", bad=True)
            return

        if not command.__doc__:
            self.notify("Command has no docstring. Try using python without -OO",
                    bad=True)
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
        pager = self.ui.open_pager()
        if self.log:
            pager.set_source(["Message Log:"] + list(self.log))
        else:
            pager.set_source(["Message Log:", "No messages!"])

    def display_file(self):
        if not self.thisfile or not self.thisfile.is_file:
            return

        pager = self.ui.open_pager()
        if self.settings.preview_images and self.thisfile.image:
            pager.set_image(self.thisfile.realpath)
        else:
            f = self.thisfile.get_preview_source(pager.wid, pager.hei)
            if self.thisfile.is_image_preview():
                pager.set_image(f)
            else:
                pager.set_source(f)

    # --------------------------
    # -- Previews
    # --------------------------
    def update_preview(self, path):
        try:
            del self.previews[path]
            self.ui.need_redraw = True
        except:
            return False

    if version_info[0] == 3:
        def sha1_encode(self, path):
            return os.path.join(ranger.CACHEDIR,
                    sha1(path.encode('utf-8')).hexdigest()) + '.jpg'
    else:
        def sha1_encode(self, path):
            return os.path.join(ranger.CACHEDIR,
                    sha1(path).hexdigest()) + '.jpg'

    def get_preview(self, file, width, height):
        pager = self.ui.get_pager()
        path = file.realpath

        if self.settings.preview_images and file.image:
            pager.set_image(path)
            return None

        if self.settings.preview_script and self.settings.use_preview_script:
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
            except:
                data = self.previews[path] = {'loading': False}
            else:
                if data['loading']:
                    return None


            found = data.get((-1, -1), data.get((width, -1),
                data.get((-1, height), data.get((width, height), False))))
            if found == False:
                try:
                    stat_ = os.stat(self.settings.preview_script)
                except:
                    self.fm.notify("Preview Script `%s' doesn't exist!" %
                            self.settings.preview_script, bad=True)
                    return None

                if not stat_.st_mode & S_IEXEC:
                    self.fm.notify("Preview Script `%s' is not executable!" %
                            self.settings.preview_script, bad=True)
                    return None

                data['loading'] = True

                cacheimg = os.path.join(ranger.CACHEDIR, self.sha1_encode(path))
                if (os.path.isfile(cacheimg) and os.path.getmtime(cacheimg) > os.path.getmtime(path)):
                    data['foundpreview'] = True
                    data['imagepreview'] = True
                    pager.set_image(cacheimg)
                    data['loading'] = False
                    return cacheimg

                loadable = CommandLoader(args=[self.settings.preview_script,
                    path, str(width), str(height), cacheimg], read=True,
                    silent=True, descr="Getting preview of %s" % path)
                def on_after(signal):
                    exit = signal.process.poll()
                    content = signal.loader.stdout_buffer
                    data['foundpreview'] = True
                    if exit == 0:
                        data[(width, height)] = content
                    elif exit == 3:
                        data[(-1, height)] = content
                    elif exit == 4:
                        data[(width, -1)] = content
                    elif exit == 5:
                        data[(-1, -1)] = content
                    elif exit == 6:
                        data['imagepreview'] = True
                    elif exit == 1:
                        data[(-1, -1)] = None
                        data['foundpreview'] = False
                    elif exit == 2:
                        f = codecs.open(path, 'r', errors='ignore')
                        try:
                            data[(-1, -1)] = f.read(1024 * 32)
                        except UnicodeDecodeError:
                            f.close()
                            f = codecs.open(path, 'r', encoding='latin-1',
                                    errors='ignore')
                            data[(-1, -1)] = f.read(1024 * 32)
                        f.close()
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
                        else:
                            pager.set_source(self.thisfile.get_preview_source(
                                pager.wid, pager.hei))
                def on_destroy(signal):
                    try:
                        del self.previews[path]
                    except:
                        pass
                loadable.signal_bind('after', on_after)
                loadable.signal_bind('destroy', on_destroy)
                self.loader.add(loadable)
                return None
            else:
                return found
        else:
            try:
                return codecs.open(path, 'r', errors='ignore')
            except:
                return None

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

    def tab_close(self, name=None):
        if name is None:
            name = self.current_tab
        tab = self.tabs[name]
        if name == self.current_tab:
            direction = -1 if name == self._get_tab_list()[-1] else 1
            previous = self.current_tab
            self.tab_move(direction)
            if previous == self.current_tab:
                return  # can't close last tab
        if name in self.tabs:
            del self.tabs[name]
        self.restorable_tabs.append(tab)

    def tab_restore(self):
        # NOTE: The name of the tab is not restored.
        previous_tab = self.thistab
        if self.restorable_tabs:
            tab = self.restorable_tabs.pop()
            for name in range(1, len(self.tabs) + 2):
                if not name in self.tabs:
                    self.current_tab = name
                    self.tabs[name] = tab
                    tab.enter_dir(tab.path, history=False)
                    self.thistab = tab
                    self.change_mode('normal')
                    self.signal_emit('tab.change', old=previous_tab,
                            new=self.thistab)
                    break

    def tab_move(self, offset, narg=None):
        if narg:
            return self.tab_open(narg)
        assert isinstance(offset, int)
        tablist = self._get_tab_list()
        current_index = tablist.index(self.current_tab)
        newtab = tablist[(current_index + offset) % len(tablist)]
        if newtab != self.current_tab:
            self.tab_open(newtab)

    def tab_new(self, path=None, narg=None):
        if narg:
            return self.tab_open(narg, path)
        for i in range(1, 10):
            if not i in self.tabs:
                return self.tab_open(i, path)

    def _get_tab_list(self):
        assert len(self.tabs) > 0, "There must be >=1 tabs at all times"
        return sorted(self.tabs)

    # --------------------------
    # -- Overview of internals
    # --------------------------

    def dump_keybindings(self, *contexts):
        if not contexts:
            contexts = 'browser', 'console', 'pager', 'taskview'

        temporary_file = tempfile.NamedTemporaryFile()
        def write(string):
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
        pager = os.environ.get('PAGER', ranger.DEFAULT_PAGER)
        self.run([pager, temporary_file.name])

    def dump_commands(self):
        temporary_file = tempfile.NamedTemporaryFile()
        def write(string):
            temporary_file.write(string.encode('utf-8'))

        undocumented = []
        for cmd_name in sorted(self.commands.commands):
            cmd = self.commands.commands[cmd_name]
            if hasattr(cmd, '__doc__') and cmd.__doc__:
                write(cleandoc(cmd.__doc__))
                write("\n\n" + "-" * 60 + "\n")
            else:
                undocumented.append(cmd)

        if undocumented:
            write("Undocumented commands:\n\n")
            for cmd in undocumented:
                write("    :%s\n" % cmd.get_name())

        temporary_file.flush()
        pager = os.environ.get('PAGER', ranger.DEFAULT_PAGER)
        self.run([pager, temporary_file.name])

    def dump_settings(self):
        temporary_file = tempfile.NamedTemporaryFile()
        def write(string):
            temporary_file.write(string.encode('utf-8'))

        for setting in sorted(ALLOWED_SETTINGS):
            write("%30s = %s\n" % (setting, getattr(self.settings, setting)))

        temporary_file.flush()
        pager = os.environ.get('PAGER', ranger.DEFAULT_PAGER)
        self.run([pager, temporary_file.name])

    # --------------------------
    # -- File System Operations
    # --------------------------

    def uncut(self):
        self.copy_buffer = set()
        self.do_cut = False
        self.ui.browser.main_column.request_redraw()

    def copy(self, mode='set', narg=None, dirarg=None):
        """Copy the selected items.  Modes are: 'set', 'add', 'remove'."""
        assert mode in ('set', 'add', 'remove')
        cwd = self.thisdir
        if not narg and not dirarg:
            selected = (f for f in self.thistab.get_selection() if f in cwd.files)
        else:
            if not dirarg and narg:
                direction = Direction(down=1)
                offset = 0
            else:
                direction = Direction(dirarg)
                offset = 1
            pos, selected = direction.select(
                    override=narg, lst=cwd.files, current=cwd.pointer,
                    pagesize=self.ui.termsize[0], offset=offset)
            cwd.pointer = pos
            cwd.correct_pointer()
        if mode == 'set':
            self.copy_buffer = set(selected)
        elif mode == 'add':
            self.copy_buffer.update(set(selected))
        elif mode == 'remove':
            self.copy_buffer.difference_update(set(selected))
        self.do_cut = False
        self.ui.browser.main_column.request_redraw()

    def cut(self, mode='set', narg=None, dirarg=None):
        self.copy(mode=mode, narg=narg, dirarg=dirarg)
        self.do_cut = True
        self.ui.browser.main_column.request_redraw()

    def paste_symlink(self, relative=False):
        copied_files = self.copy_buffer
        for f in copied_files:
            self.notify(next_available_filename(f.basename))
            try:
                new_name = next_available_filename(f.basename)
                if relative:
                    relative_symlink(f.path, join(getcwd(), new_name))
                else:
                    symlink(f.path, join(getcwd(), new_name))
            except Exception as x:
                self.notify(x)

    def paste_hardlink(self):
        for f in self.copy_buffer:
            try:
                new_name = next_available_filename(f.basename)
                link(f.path, join(getcwd(), new_name))
            except Exception as x:
                self.notify(x)

    def paste_hardlinked_subtree(self):
        for f in self.copy_buffer:
            try:
                target_path = join(getcwd(), f.basename)
                self._recurse_hardlinked_tree(f.path, target_path)
            except Exception as x:
                self.notify(x)

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

    def paste(self, overwrite=False):
        """Paste the selected items into the current directory"""
        self.loader.add(CopyLoader(self.copy_buffer, self.do_cut, overwrite))
        self.do_cut = False

    def delete(self):
        # XXX: warn when deleting mount points/unseen marked files?
        self.notify("Deleting!")
        selected = self.thistab.get_selection()
        self.copy_buffer -= set(selected)
        if selected:
            for f in selected:
                if isdir(f.path) and not os.path.islink(f.path):
                    try:
                        shutil.rmtree(f.path)
                    except OSError as err:
                        self.notify(err)
                else:
                    try:
                        os.remove(f.path)
                    except OSError as err:
                        self.notify(err)
        self.thistab.ensure_correct_pointer()

    def mkdir(self, name):
        try:
            os.mkdir(os.path.join(self.thisdir.path, name))
        except OSError as err:
            self.notify(err)

    def rename(self, src, dest):
        if hasattr(src, 'path'):
            src = src.path

        try:
            os.renames(src, dest)
        except OSError as err:
            self.notify(err)
