# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

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

DEFAULT_FOREGROUND = curses.COLOR_WHITE
DEFAULT_BACKGROUND = curses.COLOR_BLACK
COLOR_PAIRS = {10: 0}

def get_color(fg, bg):
    """Returns the curses color pair for the given fg/bg combination."""

    key = (fg, bg)
    if key not in COLOR_PAIRS:
        size = len(COLOR_PAIRS)
        try:
            curses.init_pair(size, fg, bg)
        except:
            # If curses.use_default_colors() failed during the initialization
            # of curses, then using -1 as fg or bg will fail as well, which
            # we need to handle with fallback-defaults:
            if fg == -1:  # -1 is the "default" color
                fg = DEFAULT_FOREGROUND
            if bg == -1:  # -1 is the "default" color
                bg = DEFAULT_BACKGROUND

            try:
                curses.init_pair(size, fg, bg)
            except:
                # If this fails too, colors are probably not supported
                pass
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
