import curses

class OutOfBoundsException(Exception): pass

class Widget():
	def __init__(self, win):
		self.win = win
		self.setdim(0, 0, 0, 0)

	def setdim(self, y, x, hei=None, wid=None):
		maxy, maxx = self.win.getmaxyx()
		wid = wid or maxx - x
		hei = hei or maxy - y
		if x + wid > maxx or y + hei > maxy:
			raise OutOfBoundsException()

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
