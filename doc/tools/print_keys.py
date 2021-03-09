#!/usr/bin/env python
"""
You can use this tool to find out values of keypresses
"""

from __future__ import (absolute_import, division, print_function)

import curses
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ranger.ext.keybinding_parser import special_keys, reversed_special_keys, construct_keybinding

SEPARATOR = '; '


@curses.wrapper
def main(win):
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    curses.mouseinterval(0)
    while True:
        char = win.getch()
        string = ''
        if char == curses.KEY_MOUSE:
            string = repr(curses.getmouse()) + SEPARATOR
        else:
            string = str(char) + '(%s)' % construct_keybinding(char) + SEPARATOR
        try:
            win.addstr(string)
        except curses.error:
            win.erase()
            win.addstr(string)
