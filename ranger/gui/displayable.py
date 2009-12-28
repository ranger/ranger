from ranger.shared import FileManagerAware, EnvironmentAware, SettingsAware
from ranger import log

class Displayable(EnvironmentAware, FileManagerAware, SettingsAware):
	focused = False
	visible = True
	win = None
	colorscheme = None

	def __init__(self, win, env=None, fm=None, settings=None):
		from ranger.gui.ui import UI
		if env is not None:
			self.env = env
		if fm is not None:
			self.fm = fm
		if settings is not None:
			self.settings = settings

		self.x = 0
		self.y = 0
		self.wid = 0
		self.hei = 0
		self.colorscheme = self.settings.colorscheme

		if win is not None:
			if isinstance(self, UI):
				self.win = win
			else:
				self.win = win.derwin(1, 1, 0, 0)

	def __nonzero__(self):
		"""Always True"""
		return True

	def __contains__(self, item):
		"""Is item inside the boundaries?
		item can be an iterable like [y, x] or an object with x and y methods.
		"""
		try:
			y, x = item.y, item.x
		except AttributeError:
			try:
				y, x = item
			except (ValueError, TypeError):
				return False
		
		return self.contains_point(y, x)

	def color(self, keylist = None, *keys):
		"""Change the colors from now on."""
		keys = combine(keylist, keys)
		self.win.attrset(self.colorscheme.get_attr(*keys))

	def color_at(self, y, x, wid, keylist = None, *keys):
		"""Change the colors at the specified position"""
		keys = combine(keylist, keys)
		self.win.chgat(y, x, wid, self.colorscheme.get_attr(*keys))
	
	def color_reset(self):
		"""Change the colors to the default colors"""
		Displayable.color(self, 'reset')

	def draw(self):
		"""Draw the object. Called on every main iteration.
		Containers should call draw() on their contained objects here.
		Override this!
		"""

	def destroy(self):
		"""Called when the object is destroyed.
		Override this!
		"""

	def contains_point(self, y, x):
		"""
		Test whether the point (with absolute coordinates) lies
		within the boundaries of this object.
		"""
		return (x >= self.absx and x < self.absx + self.wid) and \
				(y >= self.absy and y < self.absy + self.hei)

	def click(self, event):
		"""Called when a mouse key is pressed and self.focused is True.
		Override this!
		"""
		pass

	def press(self, key):
		"""Called when a key is pressed and self.focused is True.
		Override this!
		"""
		pass

	def activate(self, boolean):
		boolean = bool(boolean)
		self.visible = boolean
		self.focused = boolean
	
	def show(self, boolean):
		boolean = bool(boolean)
		self.visible = boolean

	def poke(self):
		"""Called before drawing, even if invisible"""
	
	def draw(self):
		"""Draw displayable.  Called on every main iteration if the object
		is visible.  Override this!
		"""
		pass

	def finalize(self):
		"""Called after every displayable is done drawing.
		Override this!
		"""
		pass

	def resize(self, y, x, hei=None, wid=None):
		"""Resize the widget"""
		try:
			maxy, maxx = self.env.termsize
		except TypeError:
			pass
		else:
			if hei is None:
				hei = maxy - y

			if wid is None:
				wid = maxx - x

			if x < 0 or y < 0:
				raise OutOfBoundsException("Starting point below zero!")

			if wid < 1 or hei < 1:
				raise OutOfBoundsException("WID and HEI must be >=1!")

			if x + wid > maxx and y + hei > maxy:
				raise OutOfBoundsException("X and Y out of bounds!")

			if x + wid > maxx:
				raise OutOfBoundsException("X out of bounds!")

			if y + hei > maxy:
				raise OutOfBoundsException("Y out of bounds!")

		try:
			self.win.resize(hei, wid)
		except:
			# Not enough space for resizing...
			try:
				self.win.mvderwin(0, 0)
				self.win.resize(hei, wid)
			except:
				raise OutOfBoundsException("Resizing Failed!")

		self.win.mvderwin(y, x)
		self.absx = x
		self.absy = y
		self.x = 0
		self.y = 0
		self.wid = wid
		self.hei = hei


class DisplayableContainer(Displayable):
	container = None
	def __init__(self, win, env=None, fm=None, settings=None):
		if env is not None:
			self.env = env
		if fm is not None:
			self.fm = fm
		if settings is not None:
			self.settings = settings

		Displayable.__init__(self, win)
		self.container = []

	def poke(self):
		"""Recursively called on objects in container"""
		for displayable in self.container:
			displayable.poke()

	def draw(self):
		"""Recursively called on visible objects in container"""
		for displayable in self.container:
			if displayable.visible:
				displayable.draw()

	def finalize(self):
		"""Recursively called on visible objects in container"""
		for displayable in self.container:
			if displayable.visible:
				displayable.finalize()
	
	def get_focused_obj(self):
		"""Finds a focused displayable object in the container."""
		for displayable in self.container:
			if displayable.focused:
				return displayable
			try:
				obj = displayable.get_focused_obj()
			except AttributeError:
				pass
			else:
				if obj is not None:
					return obj
		return None

	def press(self, key):
		"""Recursively called on objects in container"""
		focused_obj = self.get_focused_obj()

		if focused_obj:
			focused_obj.press(key)
			return True
		return False

	def click(self, event):
		"""Recursively called on objects in container"""
		focused_obj = self.get_focused_obj()
		if focused_obj and focused_obj.click(event):
			return True

		for displayable in self.container:
			if event in displayable:
				if displayable.click(event):
					return True

		return False

	def add_obj(self, *objs):
		self.container.extend(objs)

	def destroy(self):
		"""Recursively called on objects in container"""
		for displayable in self.container:
			displayable.destroy()

class OutOfBoundsException(Exception):
	pass

def combine(seq, tup):
	"""Add seq and tup. Ensures that the result is a tuple."""
	try:
		if isinstance(seq, str): raise TypeError
		return tuple(tuple(seq) + tup)
	except TypeError:
		try:
			return tuple((seq, ) + tup)
		except:
			return ()
