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

from __future__ import (absolute_import, division, print_function)

import curses

DEFAULT_FOREGROUND = curses.COLOR_WHITE
DEFAULT_BACKGROUND = curses.COLOR_BLACK
# Color pair 0 is wired to white on black and cannot be changed
COLOR_PAIRS = {(DEFAULT_FOREGROUND, DEFAULT_BACKGROUND): 0}


def get_color(fg, bg):
    """Returns the curses color pair for the given fg/bg combination."""

    key = (fg, bg)
    if key not in COLOR_PAIRS:
        size = len(COLOR_PAIRS)
        try:
            curses.init_pair(size, fg, bg)
        except ValueError:
            # We're trying to add more pairs than the terminal can store,
            # approximating to the closest color pair that's already stored
            # would be cool but the easier solution is to just fall back to the
            # default fore and background colors, pair 0
            COLOR_PAIRS[key] = 0
        except curses.error:
            # If curses.use_default_colors() failed during the initialization
            # of curses, then using -1 as fg or bg will fail as well, which
            # we need to handle with fallback-defaults:
            if fg == -1:  # -1 is the "default" color
                fg = DEFAULT_FOREGROUND
            if bg == -1:  # -1 is the "default" color
                bg = DEFAULT_BACKGROUND

            try:
                curses.init_pair(size, fg, bg)
            except curses.error:
                # If this fails too, colors are probably not supported
                pass
            COLOR_PAIRS[key] = size
        else:
            COLOR_PAIRS[key] = size

    return COLOR_PAIRS[key]


# pylint: disable=invalid-name
black = curses.COLOR_BLACK
blue = curses.COLOR_BLUE
cyan = curses.COLOR_CYAN
green = curses.COLOR_GREEN
magenta = curses.COLOR_MAGENTA
red = curses.COLOR_RED
white = curses.COLOR_WHITE
yellow = curses.COLOR_YELLOW
default = -1

normal = curses.A_NORMAL
bold = curses.A_BOLD
blink = curses.A_BLINK
reverse = curses.A_REVERSE
underline = curses.A_UNDERLINE
invisible = curses.A_INVIS
dim = curses.A_DIM

default_colors = (default, default, normal)
# pylint: enable=invalid-name

curses.setupterm()
# Adding BRIGHT to a color achieves what `bold` was used for.
BRIGHT = 8 if curses.tigetnum('colors') >= 16 else 0
