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
		for c in range(0, curses.COLORS):
			init_pair(c, c, -1)
			win.addstr(str(c) + ' ', color_pair(c) | attr)
	use_default_colors()
	win.addstr("available colors: %d\n\n" % curses.COLORS)
	print_all_colors(0)
	win.addstr("\n\n")
	print_all_colors(A_BOLD)
	win.refresh()
	win.getch()

