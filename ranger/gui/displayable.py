from ranger.shared import FileManagerAware, EnvironmentAware, SettingsAware

class Displayable(EnvironmentAware, FileManagerAware, SettingsAware):
	focused = False
	visible = True
	win = None
	colorscheme = None

	def __init__(self, win, env=None, fm=None, settings=None):
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
			self.win = win

	def __nonzero__(self):
		"""Always True"""
		return True

	def __contains__(self, item):
		"""Is item inside the boundaries?
item can be an iterable like [y, x] or an object with x and y methods."""
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
Override this!"""

	def destroy(self):
		"""Called when the object is destroyed.
Override this!"""

	def contains_point(self, y, x):
		"""Test if the point lies within the boundaries of this object"""
		return (x >= self.x and x < self.x + self.wid) and \
				(y >= self.y and y < self.y + self.hei)

	def click(self, event):
		"""Called when a mouse key is pressed and self.focused is True.
Override this!"""
		pass

	def press(self, key):
		"""Called when a key is pressed and self.focused is True.
Override this!"""
		pass
	
	def draw(self):
		"""Draw displayable. Called on every main iteration.
Override this!"""
		pass

	def finalize(self):
		"""Called after every displayable is done drawing.
Override this!"""
		pass

	def resize(self, y, x, hei=None, wid=None):
		"""Resize the widget"""
		try:
			maxy, maxx = self.env.termsize
		except TypeError:
			pass
		else:
			wid = wid or maxx - x
			hei = hei or maxy - y

			if x < 0 or y < 0:
				raise OutOfBoundsException("Starting point below zero!")

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

	def draw(self):
		"""Recursively called on objects in container"""
		for displayable in self.container:
			if displayable.visible:
				displayable.draw()

	def finalize(self):
		"""Recursively called on objects in container"""
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
