# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
# Copyright (C) 2010 David Barnett <davidbarnett2@gmail.com>
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

import curses
import _curses

from ranger.gui.color import get_color
from ranger.core.shared import SettingsAware

def _fix_surrogates(args):
	return [isinstance(arg, str) and arg.encode('utf-8', 'surrogateescape')
			.decode('utf-8', 'replace') or arg for arg in args]

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
		except:
			if len(args) > 1:
				try:
					self.win.addstr(*_fix_surrogates(args))
				except:
					pass

	def addnstr(self, *args):
		try:
			self.win.addnstr(*args)
		except:
			if len(args) > 2:
				try:
					self.win.addnstr(*_fix_surrogates(args))
				except:
					pass

	def addch(self, *args):
		try:
			self.win.addch(*args)
		except:
			pass

	def color(self, *keys):
		"""Change the colors from now on."""
		attr = self.settings.colorscheme.get_attr(*keys)
		try:
			self.win.attrset(attr)
		except _curses.error:
			pass

	def color_at(self, y, x, wid, *keys):
		"""Change the colors at the specified position"""
		attr = self.settings.colorscheme.get_attr(*keys)
		try:
			self.win.chgat(y, x, wid, attr)
		except _curses.error:
			pass

	def set_fg_bg_attr(self, fg, bg, attr):
		try:
			self.win.attrset(curses.color_pair(get_color(fg, bg)) | attr)
		except _curses.error:
			pass

	def color_reset(self):
		"""Change the colors to the default colors"""
		CursesShortcuts.color(self, 'reset')
