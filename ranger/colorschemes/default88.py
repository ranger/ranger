# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

"""
The default colorscheme, using 88 colors.

For now, just map each of the 8 base colors to new ones
for brighter blue, etc. and do some minor modifications.
"""

from ranger.gui.color import *
from ranger.colorschemes.default import Default
import curses

class Scheme(Default):
	def use(self, context):
		fg, bg, attr = Default.use(self, context)

		if curses.COLORS < 88:
			return fg, bg, attr

		try:
			translate = {
				blue: 22,
				yellow: 72,
				green: 20,
				cyan: 21,
				white: 79,
				red: 32,
				magenta: magenta,
			}
			fg = translate[fg]
		except KeyError:
			pass

		if context.in_browser:
			if context.main_column and context.marked:
				if context.selected:
					fg = 77
				else:
					fg = 68
					attr |= reverse

		return fg, bg, attr

