
class OutOfBoundsException(Exception):
	pass

def combine(keylist, keys):
	if type(keylist) in (list, tuple):
		return tuple(tuple(keylist) + keys)
	else:
		return tuple((keylist, ) + keys)

from ranger.shared import SettingsAware
class Widget(SettingsAware):
	def __init__(self, win, _):
		self.win = win
		self.focused = False
		self.colorscheme = self.settings.colorscheme
		self.visible = True
		self.setdim(0, 0, 0, 0)

	def color(self, keylist = None, *keys):
		keys = combine(keylist, keys)
		self.win.attrset(self.colorscheme.get_attr(*keys))

	def color_at(self, y, x, wid, keylist = None, *keys):
		keys = combine(keylist, keys)
		self.win.chgat(y, x, wid, self.colorscheme.get_attr(*keys))
	
	def color_reset(self):
		Widget.color(self, 'reset')

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

	def feed_env(self, env):
		pass

	def feed(self):
		pass

	def click(self, event, fm):
		pass

	def press(self, key, fm):
		pass
	
	def draw(self):
		pass

	def finalize(self):
		pass

	def destroy(self):
		pass
