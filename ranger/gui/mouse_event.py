class MouseEvent(object):
	import curses
	PRESSED = [ 0,
			curses.BUTTON1_PRESSED,
			curses.BUTTON2_PRESSED,
			curses.BUTTON3_PRESSED,
			curses.BUTTON4_PRESSED ]

	def __init__(self, getmouse):
		_, self.x, self.y, _, self.bstate = getmouse
	
	def pressed(self, n):
		try:
			return (self.bstate & MouseEvent.PRESSED[n]) != 0
		except:
			return False
