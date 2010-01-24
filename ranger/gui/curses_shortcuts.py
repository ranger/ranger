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

import _curses

from ranger.ext.iter_tools import flatten
from ranger.shared import SettingsAware

class CursesShortcuts(SettingsAware):
	"""
	This class defines shortcuts to faciliate operations with curses.
	color(*keys) -- sets the color associated with the keys from
		the current colorscheme.
	color_at(y, x, wid, *keys) -- sets the color at the given position
	color_reset() -- resets the color to the default
	addstr(*args) -- failsafe version of self.win.addstr(*args)
	"""

	def addstr(self, *args):
		try:
			self.win.addstr(*args)
		except (_curses.error, TypeError):
			pass

	def addnstr(self, *args):
		try:
			self.win.addnstr(*args)
		except (_curses.error, TypeError):
			pass

	def color(self, *keys):
		"""Change the colors from now on."""
		keys = flatten(keys)
		attr = self.settings.colorscheme.get_attr(*keys)
		try:
			self.win.attrset(attr)
		except _curses.error:
			pass

	def color_at(self, y, x, wid, *keys):
		"""Change the colors at the specified position"""
		keys = flatten(keys)
		attr = self.settings.colorscheme.get_attr(*keys)
		try:
			self.win.chgat(y, x, wid, attr)
		except _curses.error:
			pass

	def color_reset(self):
		"""Change the colors to the default colors"""
		CursesShortcuts.color(self, 'reset')
