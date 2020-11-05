#!/usr/bin/env python
"""
You can use this tool to find out values of keypresses
"""

from __future__ import (absolute_import, division, print_function)

import curses


SEPARATOR = '; '


@curses.wrapper
def main(window):
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    curses.mouseinterval(0)
    while True:
        char = window.getch()
        if char == curses.KEY_MOUSE:
            window.addstr(repr(curses.getmouse()) + SEPARATOR)
        else:
            window.addstr(str(char) + SEPARATOR)
