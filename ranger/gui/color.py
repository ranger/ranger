import curses

COLOR_PAIRS = {10: 0}

def get_color(fg, bg):
	import curses

	c = bg+2 + 9*(fg + 2)

	if c not in COLOR_PAIRS:
		size = len(COLOR_PAIRS)
		curses.init_pair(size, fg, bg)
		COLOR_PAIRS[c] = size

	return COLOR_PAIRS[c]

black   = curses.COLOR_BLACK
blue    = curses.COLOR_BLUE
cyan    = curses.COLOR_CYAN
green   = curses.COLOR_GREEN
magenta = curses.COLOR_MAGENTA
red     = curses.COLOR_RED
white   = curses.COLOR_WHITE
yellow  = curses.COLOR_YELLOW
default = -1

normal     = curses.A_NORMAL
bold       = curses.A_BOLD
reverse    = curses.A_REVERSE
underline  = curses.A_UNDERLINE
invisible  = curses.A_INVIS

default_colors = (default, default, normal)
