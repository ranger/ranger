#!/usr/bin/env python
"""
You can use this tool to find out values of keypresses
"""

from curses import *

sep = '; '

@wrapper
def main(w):
	while True:
		w.addstr(str(w.getch()) + sep)

