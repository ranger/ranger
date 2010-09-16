# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Some experimental colorscheme.
"""

from ranger.gui.color import *
from ranger.colorschemes.default import Default
import curses

class Scheme(Default):
	def use(self, context):
		fg, bg, attr = Default.use(self, context)

		if curses.COLORS < 88:
			return fg, bg, attr

		dircolor = 77
		dircolor_selected = {True: 79, False: 78}
		linkcolor = {True: 21, False: 48}

		if context.in_browser:
			if context.media:
				if context.image:
					fg = 20
				elif context.video:
					fg = 22
				elif context.audio:
					fg = 23

			if context.container:
				fg = 32
			if context.directory:
				fg = dircolor
				if context.selected:
					fg = dircolor_selected[context.main_column]
			elif context.executable and not \
					any((context.media, context.container)):
				fg = 82
			if context.link:
				fg = linkcolor[context.good]

			if context.main_column:
				if context.selected:
					attr |= bold
				if context.marked:
					attr |= bold
					fg = 53

		if context.in_titlebar:
			if context.hostname:
				fg = context.bad and 48 or 82
			elif context.directory:
				fg = dircolor
			elif context.link:
				fg = linkcolor[True]

		return fg, bg, attr
