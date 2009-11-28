import curses
from ranger.gui.color import color_pairs

class OutOfBoundsException(Exception): pass

class Widget():
	def __init__(self, win):
		self.win = win
		self.setdim(0, 0, 0, 0)

	def get_color(self, fg, bg):
		c = bg+2 + 9*(fg + 2)
		try:
			return color_pairs[c]
		except KeyError:
			size = len(color_pairs)
			curses.init_pair(size, fg, bg)
			color_pairs[c] = size
			return color_pairs[c]

	def color(self, fg = -1, bg = -1, attr = 0):
		self.win.attrset(attr | curses.color_pair(self.get_color(fg, bg)))

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
