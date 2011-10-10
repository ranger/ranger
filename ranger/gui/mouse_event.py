# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
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

class MouseEvent(object):
	PRESSED = [ 0,
			curses.BUTTON1_PRESSED,
			curses.BUTTON2_PRESSED,
			curses.BUTTON3_PRESSED,
			curses.BUTTON4_PRESSED ]
	CTRL_SCROLLWHEEL_MULTIPLIER = 5

	def __init__(self, getmouse):
		"""Creates a MouseEvent object from the result of win.getmouse()"""
		_, self.x, self.y, _, self.bstate = getmouse

		# x-values above ~220 suddenly became negative, apparently
		# it's sufficient to add 0xFF to fix that error.
		if self.x < 0:
			self.x += 0xFF

		if self.y < 0:
			self.y += 0xFF

	def pressed(self, n):
		"""Returns whether the mouse key n is pressed"""
		try:
			return (self.bstate & MouseEvent.PRESSED[n]) != 0
		except:
			return False

	def mouse_wheel_direction(self):
		"""Returns the direction of the scroll action, 0 if there was none"""
		# If the bstate > ALL_MOUSE_EVENTS, it's an invalid mouse button.
		# I interpret invalid buttons as "scroll down" because all tested
		# systems have a broken curses implementation and this is a workaround.
		if self.bstate & curses.BUTTON4_PRESSED:
			return self.ctrl() and -self.CTRL_SCROLLWHEEL_MULTIPLIER or -1
		elif self.bstate & curses.BUTTON2_PRESSED \
				or self.bstate > curses.ALL_MOUSE_EVENTS:
			return self.ctrl() and self.CTRL_SCROLLWHEEL_MULTIPLIER or 1
		else:
			return 0

	def ctrl(self):
		return self.bstate & curses.BUTTON_CTRL

	def alt(self):
		return self.bstate & curses.BUTTON_ALT

	def shift(self):
		return self.bstate & curses.BUTTON_SHIFT

	def key_invalid(self):
		return self.bstate > curses.ALL_MOUSE_EVENTS
