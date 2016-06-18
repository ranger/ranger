#!/usr/bin/env python
"""
You can use this tool to find out values of keypresses
"""

from curses import *

sep = '; '


@wrapper
def main(w):
    mousemask(ALL_MOUSE_EVENTS)
    mouseinterval(0)
    while True:
        ch = w.getch()
        if ch == KEY_MOUSE:
            w.addstr(repr(getmouse()) + sep)
        else:
            w.addstr(str(ch) + sep)
