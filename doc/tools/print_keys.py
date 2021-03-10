#!/usr/bin/env python
"""
You can use this tool to find out values of keypresses
"""

from __future__ import (absolute_import, division, print_function)

import curses
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ranger.ext.keybinding_parser import construct_keybinding


os.environ.setdefault('ESCDELAY', '25')
SEPARATOR = '; '


@curses.wrapper
def main(win):
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    curses.mouseinterval(0)

    while True:
        char = win.getch()
        string = ''
        if char == curses.KEY_MOUSE:
            string = 'MouseEvent' + repr(curses.getmouse())
        else:
            string = str(char) + ' => ' + repr(construct_keybinding(char))

        try:
            win.addstr(string + SEPARATOR)
        except curses.error:
            win.erase()
            win.addstr(string + SEPARATOR)
