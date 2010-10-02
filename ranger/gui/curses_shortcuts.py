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

import _curses

from ranger.ext.iter_tools import flatten
from ranger.core.shared import SettingsAware

def ascii_only(string):
	# Some python versions have problems with invalid unicode strings.
	# I think this exception is rare enough that this naive hack is enough.
	# It simply removes all non-ascii chars from a string.
	def validate_char(char):
		try:
			if ord(char) > 127:
				return '?'
		except:
			return '?'
		return char
	if isinstance(string, str):
		return ''.join(validate_char(c) for c in string)
	return string


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
		except UnicodeEncodeError:
			try:
				self.win.addstr(*(ascii_only(obj) for obj in args))
			except (_curses.error, TypeError):
				pass

	def addnstr(self, *args):
		try:
			self.win.addnstr(*args)
		except (_curses.error, TypeError):
			pass
		except UnicodeEncodeError:
			try:
				self.win.addnstr(*(ascii_only(obj) for obj in args))
			except (_curses.error, TypeError):
				pass

	def addch(self, *args):
		try:
			self.win.addch(*args)
		except (_curses.error, TypeError):
			pass
		except UnicodeEncodeError:
			try:
				self.win.addch(*(ascii_only(obj) for obj in args))
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
