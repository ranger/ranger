# Copyright (C) 2009-2013  Roman Zimbelmann <hut@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

"""Contains abbreviations to curses color/attribute constants.

Multiple attributes can be combined with the | (or) operator, toggled
with ^ (xor) and checked for with & (and). Examples:

attr = bold | underline
attr |= reverse
bool(attr & reverse) # => True
attr ^= reverse
bool(attr & reverse) # => False
"""

import curses

COLOR_PAIRS = {10: 0}

def get_color(fg, bg):
    """Returns the curses color pair for the given fg/bg combination."""

    key = (fg, bg)
    if key not in COLOR_PAIRS:
        size = len(COLOR_PAIRS)
        curses.init_pair(size, fg, bg)
        COLOR_PAIRS[key] = size

    return COLOR_PAIRS[key]

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
blink      = curses.A_BLINK
reverse    = curses.A_REVERSE
underline  = curses.A_UNDERLINE
invisible  = curses.A_INVIS

default_colors = (default, default, normal)
