#!/usr/bin/env python
"""
You can use this tool to display all supported colors and their color number.
It will exit after a keypress.
"""

from __future__ import (absolute_import, print_function)

import curses


@curses.wrapper
def main(win):
    def print_all_colors(attr):
        for color in range(-1, curses.COLORS):
            try:
                curses.init_pair(color, color, 0)
            except Exception:
                pass
            else:
                win.addstr(str(color) + ' ', curses.color_pair(color) | attr)
    curses.start_color()
    try:
        curses.use_default_colors()
    except Exception:
        pass
    win.addstr("available colors: %d\n\n" % curses.COLORS)
    print_all_colors(0)
    win.addstr("\n\n")
    print_all_colors(curses.A_BOLD)
    win.refresh()
    win.getch()
