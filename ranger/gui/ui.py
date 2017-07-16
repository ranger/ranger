# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

import os
import sys
import threading
import curses
from subprocess import CalledProcessError

from ranger.ext.keybinding_parser import KeyBuffer, KeyMaps, ALT_KEY
from ranger.ext.lazy_property import lazy_property
from ranger.ext.signals import Signal
from ranger.ext.spawn import check_output

from .displayable import DisplayableContainer
from .mouse_event import MouseEvent


MOUSEMASK = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION

_ASCII = ''.join(chr(c) for c in range(32, 127))


def ascii_only(string):
    return ''.join(c if c in _ASCII else '?' for c in string)


def _setup_mouse(signal):
    if signal['value']:
        curses.mousemask(MOUSEMASK)
        curses.mouseinterval(0)

        # This line solves this problem:
        # If a mouse click triggers an action that disables curses and
        # starts curses again, (e.g. running a ## file by clicking on its
        # preview) and the next key is another mouse click, the bstate of this
        # mouse event will be invalid.  (atm, invalid bstates are recognized
        # as scroll-down, so this avoids an errorneous scroll-down action)
        curses.ungetmouse(0, 0, 0, 0, 0)
    else:
        curses.mousemask(0)


class UI(  # pylint: disable=too-many-instance-attributes,too-many-public-methods
        DisplayableContainer):
    ALLOWED_VIEWMODES = 'miller', 'multipane'

    is_set_up = False
    load_mode = False
    is_on = False
    termsize = None

    def __init__(self, env=None, fm=None):  # pylint: disable=super-init-not-called
        self.keybuffer = KeyBuffer()
        self.keymaps = KeyMaps(self.keybuffer)
        self.redrawlock = threading.Event()
        self.redrawlock.set()

        self.titlebar = None
        self._viewmode = None
        self.taskview = None
        self.status = None
        self.console = None
        self.pager = None
        self._draw_title = None
        self._tmux_automatic_rename = None
        self.browser = None

        if fm is not None:
            self.fm = fm

    def setup_curses(self):
        os.environ['ESCDELAY'] = '25'   # don't know a cleaner way
        try:
            self.win = curses.initscr()
        except curses.error as ex:
            if ex.args[0] == "setupterm: could not find terminal":
                os.environ['TERM'] = 'linux'
                self.win = curses.initscr()
        self.keymaps.use_keymap('browser')
        DisplayableContainer.__init__(self, None)

    def initialize(self):
        """initialize curses, then call setup (at the first time) and resize."""
        self.win.leaveok(0)
        self.win.keypad(1)
        self.load_mode = False

        curses.cbreak()
        curses.noecho()
        curses.halfdelay(20)
        try:
            curses.curs_set(int(bool(self.settings.show_cursor)))
        except curses.error:
            pass
        curses.start_color()
        try:
            curses.use_default_colors()
        except curses.error:
            pass

        self.settings.signal_bind('setopt.mouse_enabled', _setup_mouse)
        self.settings.signal_bind('setopt.freeze_files', self.redraw_statusbar)
        _setup_mouse(dict(value=self.settings.mouse_enabled))

        if not self.is_set_up:
            self.is_set_up = True
            self.setup()
            self.win.addstr("loading...")
            self.win.refresh()
            self._draw_title = curses.tigetflag('hs')  # has_status_line

            # Save tmux setting `automatic-rename`
            if self.settings.update_tmux_title:
                try:
                    self._tmux_automatic_rename = check_output(
                        ['tmux', 'show-window-options', '-v', 'automatic-rename']).strip()
                except CalledProcessError:
                    self._tmux_automatic_rename = None

        self.update_size()
        self.is_on = True

        if self.settings.update_tmux_title:
            sys.stdout.write("\033kranger\033\\")
            sys.stdout.flush()

        if 'vcsthread' in self.__dict__:
            self.vcsthread.unpause()

    def suspend(self):
        """Turn off curses"""
        if 'vcsthread' in self.__dict__:
            self.vcsthread.pause()
            self.vcsthread.paused.wait()

        self.win.keypad(0)
        curses.nocbreak()
        curses.echo()
        try:
            curses.curs_set(1)
        except curses.error:
            pass
        if self.settings.mouse_enabled:
            _setup_mouse(dict(value=False))
        curses.endwin()
        self.is_on = False

    def set_load_mode(self, boolean):
        boolean = bool(boolean)
        if boolean != self.load_mode:
            self.load_mode = boolean

            if boolean:
                # don't wait for key presses in the load mode
                curses.cbreak()
                self.win.nodelay(1)
            else:
                self.win.nodelay(0)
                # Sanitize halfdelay setting
                halfdelay = min(255, max(1, self.settings.idle_delay // 100))
                curses.halfdelay(halfdelay)

    def destroy(self):
        """Destroy all widgets and turn off curses"""
        if 'vcsthread' in self.__dict__:
            if not self.vcsthread.stop():
                self.fm.notify('Failed to stop `UI.vcsthread`', bad=True)
            del self.__dict__['vcsthread']
        DisplayableContainer.destroy(self)

        # Restore tmux setting `automatic-rename`
        if self.settings.update_tmux_title:
            if self._tmux_automatic_rename:
                try:
                    check_output(['tmux', 'set-window-option',
                                  'automatic-rename', self._tmux_automatic_rename])
                except CalledProcessError:
                    pass
            else:
                try:
                    check_output(['tmux', 'set-window-option', '-u', 'automatic-rename'])
                except CalledProcessError:
                    pass

        self.suspend()

    def handle_mouse(self):
        """Handles mouse input"""
        try:
            event = MouseEvent(curses.getmouse())
        except curses.error:
            return
        if not self.console.visible:
            DisplayableContainer.click(self, event)

    def handle_key(self, key):
        """Handles key input"""
        self.hint()

        if key < 0:
            self.keybuffer.clear()

        elif not DisplayableContainer.press(self, key):
            self.keymaps.use_keymap('browser')
            self.press(key)

    def press(self, key):
        keybuffer = self.keybuffer
        self.status.clear_message()

        keybuffer.add(key)
        self.fm.hide_bookmarks()
        self.browser.draw_hints = not keybuffer.finished_parsing \
            and keybuffer.finished_parsing_quantifier

        if keybuffer.result is not None:
            try:
                self.fm.execute_console(
                    keybuffer.result,
                    wildcards=keybuffer.wildcards,
                    quantifier=keybuffer.quantifier,
                )
            finally:
                if keybuffer.finished_parsing:
                    keybuffer.clear()
        elif keybuffer.finished_parsing:
            keybuffer.clear()
            return False
        return True

    def handle_keys(self, *keys):
        for key in keys:
            self.handle_key(key)

    def handle_input(self):
        key = self.win.getch()
        if key == 27 or (key >= 128 and key < 256):
            # Handle special keys like ALT+X or unicode here:
            keys = [key]
            previous_load_mode = self.load_mode
            self.set_load_mode(True)
            for _ in range(4):
                getkey = self.win.getch()
                if getkey != -1:
                    keys.append(getkey)
            if len(keys) == 1:
                keys.append(-1)
            elif keys[0] == 27:
                keys[0] = ALT_KEY
            if self.settings.xterm_alt_key:
                if len(keys) == 2 and keys[1] in range(127, 256):
                    if keys[0] == 195:
                        keys = [ALT_KEY, keys[1] - 64]
                    elif keys[0] == 194:
                        keys = [ALT_KEY, keys[1] - 128]
            self.handle_keys(*keys)
            self.set_load_mode(previous_load_mode)
            if self.settings.flushinput and not self.console.visible:
                curses.flushinp()
        else:
            # Handle simple key presses, CTRL+X, etc here:
            if key >= 0:
                if self.settings.flushinput and not self.console.visible:
                    curses.flushinp()
                if key == curses.KEY_MOUSE:
                    self.handle_mouse()
                elif key == curses.KEY_RESIZE:
                    self.update_size()
                else:
                    if not self.fm.input_is_blocked():
                        self.handle_key(key)

    def setup(self):
        """Build up the UI by initializing widgets."""
        from ranger.gui.widgets.titlebar import TitleBar
        from ranger.gui.widgets.console import Console
        from ranger.gui.widgets.statusbar import StatusBar
        from ranger.gui.widgets.taskview import TaskView
        from ranger.gui.widgets.pager import Pager

        # Create a titlebar
        self.titlebar = TitleBar(self.win)
        self.add_child(self.titlebar)

        # Create the browser view
        self.settings.signal_bind('setopt.viewmode', self._set_viewmode)
        self._viewmode = None
        # The following line sets self.browser implicitly through the signal
        self.viewmode = self.settings.viewmode
        self.add_child(self.browser)

        # Create the process manager
        self.taskview = TaskView(self.win)
        self.taskview.visible = False
        self.add_child(self.taskview)

        # Create the status bar
        self.status = StatusBar(self.win, self.browser.main_column)
        self.add_child(self.status)

        # Create the console
        self.console = Console(self.win)
        self.add_child(self.console)
        self.console.visible = False

        # Create the pager
        self.pager = Pager(self.win)
        self.pager.visible = False
        self.add_child(self.pager)

    @lazy_property
    def vcsthread(self):
        """VCS thread"""
        from ranger.ext.vcs import VcsThread
        thread = VcsThread(self)
        thread.start()
        return thread

    def redraw(self):
        """Redraw all widgets"""
        self.redrawlock.wait()
        self.redrawlock.clear()
        self.poke()

        # determine which widgets are shown
        if self.console.wait_for_command_input or self.console.question_queue:
            self.console.focused = True
            self.console.visible = True
            self.status.visible = False
        else:
            self.console.focused = False
            self.console.visible = False
            self.status.visible = True

        self.draw()
        self.finalize()
        self.redrawlock.set()

    def redraw_window(self):
        """Redraw the window. This only calls self.win.redrawwin()."""
        self.win.erase()
        self.win.redrawwin()
        self.win.refresh()
        self.win.redrawwin()
        self.need_redraw = True

    def update_size(self):
        """resize all widgets"""
        self.termsize = self.win.getmaxyx()
        y, x = self.termsize

        self.browser.resize(self.settings.status_bar_on_top and 2 or 1, 0, y - 2, x)
        self.taskview.resize(1, 0, y - 2, x)
        self.pager.resize(1, 0, y - 2, x)
        self.titlebar.resize(0, 0, 1, x)
        self.status.resize(self.settings.status_bar_on_top and 1 or y - 1, 0, 1, x)
        self.console.resize(y - 1, 0, 1, x)

    def draw(self):
        """Draw all objects in the container"""
        self.win.touchwin()
        DisplayableContainer.draw(self)
        if self._draw_title and self.settings.update_title:
            cwd = self.fm.thisdir.path
            if cwd.startswith(self.fm.home_path):
                cwd = '~' + cwd[len(self.fm.home_path):]
            if self.settings.shorten_title:
                split = cwd.rsplit(os.sep, self.settings.shorten_title)
                if os.sep in split[0]:
                    cwd = os.sep.join(split[1:])
            try:
                fixed_cwd = cwd.encode('utf-8', 'surrogateescape'). \
                    decode('utf-8', 'replace')
                fmt_tup = (
                    curses.tigetstr('tsl').decode('latin-1'),
                    fixed_cwd,
                    curses.tigetstr('fsl').decode('latin-1'),
                )
            except UnicodeError:
                pass
            else:
                sys.stdout.write("%sranger:%s%s" % fmt_tup)
                sys.stdout.flush()

        self.win.refresh()

    def finalize(self):
        """Finalize every object in container and refresh the window"""
        DisplayableContainer.finalize(self)
        self.win.refresh()

    def draw_images(self):
        if self.pager.visible:
            self.pager.draw_image()
        elif self.browser.pager:
            if self.browser.pager.visible:
                self.browser.pager.draw_image()
            else:
                self.browser.columns[-1].draw_image()

    def close_pager(self):
        if self.console.visible:
            self.console.focused = True
        self.pager.close()
        self.pager.visible = False
        self.pager.focused = False
        self.browser.visible = True

    def open_pager(self):
        self.browser.columns[-1].clear_image(force=True)
        if self.console.focused:
            self.console.focused = False
        self.pager.open()
        self.pager.visible = True
        self.pager.focused = True
        self.browser.visible = False
        return self.pager

    def open_embedded_pager(self):
        self.browser.open_pager()
        for column in self.browser.columns:
            if column == self.browser.main_column:
                break
            column.level_shift(amount=1)
        return self.browser.pager

    def close_embedded_pager(self):
        self.browser.close_pager()
        for column in self.browser.columns:
            column.level_restore()

    def open_console(self, string='', prompt=None, position=None):
        if self.console.open(string, prompt=prompt, position=position):
            self.status.msg = None

    def close_console(self):
        self.console.close()
        self.close_pager()

    def open_taskview(self):
        self.browser.columns[-1].clear_image(force=True)
        self.pager.close()
        self.pager.visible = False
        self.pager.focused = False
        self.console.visible = False
        self.browser.visible = False
        self.taskview.visible = True
        self.taskview.focused = True

    def redraw_main_column(self):
        self.browser.main_column.need_redraw = True

    def redraw_statusbar(self):
        self.status.need_redraw = True

    def close_taskview(self):
        self.taskview.visible = False
        self.browser.visible = True
        self.taskview.focused = False

    def throbber(self, string='.', remove=False):
        if remove:
            self.titlebar.throbber = type(self.titlebar).throbber
        else:
            self.titlebar.throbber = string

    def hint(self, text=None):
        self.status.hint = text

    def get_pager(self):
        if self.browser.pager and self.browser.pager.visible:
            return self.browser.pager
        return self.pager

    def _get_viewmode(self):
        return self._viewmode

    def _set_viewmode(self, value):
        if isinstance(value, Signal):
            value = value.value
        if value == '':
            value = self.ALLOWED_VIEWMODES[0]
        if value in self.ALLOWED_VIEWMODES:
            if self._viewmode != value:
                self._viewmode = value
                new_browser = self._viewmode_to_class(value)(self.win)

                if self.browser is None:
                    self.add_child(new_browser)
                else:
                    old_size = self.browser.y, self.browser.x, self.browser.hei, self.browser.wid
                    self.replace_child(self.browser, new_browser)
                    self.browser.destroy()
                    new_browser.resize(*old_size)

                self.browser = new_browser
                self.redraw_window()
        else:
            raise ValueError("Attempting to set invalid viewmode `%s`, should "
                             "be one of `%s`." % (value, "`, `".join(self.ALLOWED_VIEWMODES)))

    viewmode = property(_get_viewmode, _set_viewmode)

    @staticmethod
    def _viewmode_to_class(viewmode):
        if viewmode == 'miller':
            from ranger.gui.widgets.view_miller import ViewMiller
            return ViewMiller
        if viewmode == 'multipane':
            from ranger.gui.widgets.view_multipane import ViewMultipane
            return ViewMultipane
