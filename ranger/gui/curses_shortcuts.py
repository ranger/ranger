# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

import curses
import _curses
import sys

from ranger.gui.color import get_color
from ranger.core.shared import SettingsAware

REVERSE_ADDCH_ARGS = sys.version[0:5] == '3.4.0'


def _fix_surrogates(args):
    return [isinstance(arg, str) and arg.encode('utf-8', 'surrogateescape')
            .decode('utf-8', 'replace') or arg for arg in args]


class CursesShortcuts(SettingsAware):
    """This class defines shortcuts to facilitate operations with curses.

    color(*keys) -- sets the color associated with the keys from
        the current colorscheme.
    color_at(y, x, wid, *keys) -- sets the color at the given position
    color_reset() -- resets the color to the default
    addstr(*args) -- failsafe version of self.win.addstr(*args)
    """

    def addstr(self, *args):
        y, x = self.win.getyx()

        try:
            self.win.addstr(*args)
        except Exception:
            if len(args) > 1:
                self.win.move(y, x)

                try:
                    self.win.addstr(*_fix_surrogates(args))
                except Exception:
                    pass

    def addnstr(self, *args):
        y, x = self.win.getyx()

        try:
            self.win.addnstr(*args)
        except Exception:
            if len(args) > 2:
                self.win.move(y, x)

                try:
                    self.win.addnstr(*_fix_surrogates(args))
                except Exception:
                    pass

    def addch(self, *args):
        if REVERSE_ADDCH_ARGS and len(args) >= 3:
            args = [args[1], args[0]] + list(args[2:])
        try:
            self.win.addch(*args)
        except Exception:
            pass

    def color(self, *keys):
        """Change the colors from now on."""
        attr = self.settings.colorscheme.get_attr(*keys)
        try:
            self.win.attrset(attr)
        except _curses.error:
            pass

    def color_at(self, y, x, wid, *keys):
        """Change the colors at the specified position"""
        attr = self.settings.colorscheme.get_attr(*keys)
        try:
            self.win.chgat(y, x, wid, attr)
        except _curses.error:
            pass

    def set_fg_bg_attr(self, fg, bg, attr):
        try:
            self.win.attrset(curses.color_pair(get_color(fg, bg)) | attr)
        except _curses.error:
            pass

    def color_reset(self):
        """Change the colors to the default colors"""
        CursesShortcuts.color(self, 'reset')
