import curses
from ranger.gui.colorscheme import get_color

class OutOfBoundsException(Exception): pass

class Widget():
	def __init__(self, win, colorscheme):
		self.win = win
		self.colorscheme = colorscheme
		self.setdim(0, 0, 0, 0)

	def color(self, fg = -1, bg = -1, attr = 0):
		self.win.attrset(attr | curses.color_pair(get_color(fg, bg)))

	def setdim(self, y, x, hei=None, wid=None):
		maxy, maxx = self.win.getmaxyx()
		wid = wid or maxx - x
		hei = hei or maxy - y
		if x + wid > maxx and y + hei > maxy:
			raise OutOfBoundsException("X and Y out of bounds!")
		if x + wid > maxx:
			raise OutOfBoundsException("X out of bounds!")
		if y + hei > maxy:
			raise OutOfBoundsException("Y out of bounds!")

		self.x = x
		self.y = y
		self.wid = wid
		self.hei = hei
	
	def contains_point(self, y, x):
		return (x >= self.x and x < self.x + self.wid) and \
				(y >= self.y and y < self.y + self.hei)

	def feed_env(self):
		pass

	def feed(self):
		pass

	def click(self):
		pass
	
	def draw(self):
		pass

	def destroy(self):
		pass
