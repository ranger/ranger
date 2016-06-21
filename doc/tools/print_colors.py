#!/usr/bin/env python
"""
You can use this tool to display all supported colors and their color number.
It will exit after a keypress.
"""

import curses
from curses import *


@wrapper
def main(win):
    def print_all_colors(attr):
        for c in range(-1, curses.COLORS):
            try:
                init_pair(c, c, 0)
            except Exception:
                pass
            else:
                win.addstr(str(c) + ' ', color_pair(c) | attr)
    start_color()
    try:
        use_default_colors()
    except Exception:
        pass
    win.addstr("available colors: %d\n\n" % curses.COLORS)
    print_all_colors(0)
    win.addstr("\n\n")
    print_all_colors(A_BOLD)
    win.refresh()
    win.getch()
