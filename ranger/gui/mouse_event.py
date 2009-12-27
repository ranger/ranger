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
