# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
Contains abbreviations to curses color/attribute constants.

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
	"""
	Returns the curses color pair for the given fg/bg combination.
	"""

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

def remove_attr(integer, attr):
	"""Remove an attribute from an integer"""
	if integer & attribute:
		return integer ^ attribute
	return integer
