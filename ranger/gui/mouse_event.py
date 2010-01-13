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

import curses

class MouseEvent(object):
	PRESSED = [ 0,
			curses.BUTTON1_PRESSED,
			curses.BUTTON2_PRESSED,
			curses.BUTTON3_PRESSED,
			curses.BUTTON4_PRESSED ]

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

	def ctrl(self):
		return self.bstate & curses.BUTTON_CTRL

	def alt(self):
		return self.bstate & curses.BUTTON_ALT

	def shift(self):
		return self.bstate & curses.BUTTON_SHIFT

	def key_invalid(self):
		return self.bstate > curses.ALL_MOUSE_EVENTS
