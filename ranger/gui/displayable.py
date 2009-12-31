from ranger.shared import FileManagerAware, EnvironmentAware, SettingsAware
from ranger import log
import _curses

class Displayable(EnvironmentAware, FileManagerAware, SettingsAware):
	"""
	Displayables are objects which are displayed on the screen.

	This is just the abstract class, defining basic operations
	such as resizing, printing, changing colors.
	Subclasses of displayable should implement this interface:

	draw() -- draw the object here. Is only called if visible.
	poke() -- is called just before draw(), even if not visible.
	finalize() -- called after all objects finished drawing.
	click(event) -- called with a MouseEvent. This is called on all
		visible objects under the mouse, until one returns True.
	press(key) -- called after a key press on focused objects.
	destroy() -- called before destroying the displayable object

	This abstract class defines the following (helper) methods:

	color(*keys) -- sets the color associated with the keys from
		the current colorscheme.
	color_at(y, x, wid, *keys) -- sets the color at the given position
	color_reset() -- resets the color to the default
	addstr(*args) -- failsafe version of self.win.addstr(*args)
	__contains__(item) -- is the item (y, x) inside the widget?
	
	These attributes are set:

	Modifiable:
		focused -- Focused objects receive press() calls.
		visible -- Visible objects receive draw() and finalize() calls
	
	Read-Only: (i.e. reccomended not to change manually)
		win -- the own curses window object
		parent -- the parent (DisplayableContainer) object or None
		x, y, wid, hei -- absolute coordinates and boundaries
		settings, fm, env -- inherited shared variables
	"""

	def __init__(self, win, env=None, fm=None, settings=None):
		from ranger.gui.ui import UI
		if env is not None:
			self.env = env
		if fm is not None:
			self.fm = fm
		if settings is not None:
			self.settings = settings

		self.focused = False
		self.visible = True
		self.x = 0
		self.y = 0
		self.wid = 0
		self.hei = 0
		self.parent = None

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

	def addstr(self, *args):
		try:
			self.win.addstr(*args)
		except _curses.error:
			pass
	
	def color(self, keylist = None, *keys):
		"""Change the colors from now on."""
		keys = combine(keylist, keys)
		attr = self.settings.colorscheme.get_attr(*keys)
		try:
			self.win.attrset(attr)
		except _curses.error:
			pass

	def color_at(self, y, x, wid, keylist = None, *keys):
		"""Change the colors at the specified position"""
		keys = combine(keylist, keys)
		attr = self.settings.colorscheme.get_attr(*keys)
		try:
			self.win.chgat(y, x, wid, attr)
		except _curses.error:
			pass
	
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
		return (x >= self.x and x < self.x + self.wid) and \
				(y >= self.y and y < self.y + self.hei)

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
		do_move = False
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

			#if wid < 1 or hei < 1:
			#	raise OutOfBoundsException("WID and HEI must be >=1!")

			if x + wid > maxx and y + hei > maxy:
				raise OutOfBoundsException("X and Y out of bounds!")

			if x + wid > maxx:
				raise OutOfBoundsException("X out of bounds!")

			if y + hei > maxy:
				raise OutOfBoundsException("Y out of bounds!")

		if hei != self.hei or wid != self.wid:
			try:
				self.win.resize(hei, wid)
			except:
				# Not enough space for resizing...
				try:
					self.win.mvderwin(0, 0)
					do_move = True
					self.win.resize(hei, wid)
				except:
					pass
					#raise OutOfBoundsException("Resizing Failed!")

			self.hei, self.wid = self.win.getmaxyx()

		if do_move or y != self.y or x != self.x:
			log("moving " + self.__class__.__name__)
			try:
				self.win.mvderwin(y, x)
			except:
				pass

			self.y, self.x = self.win.getparyx()
			if self.parent:
				self.y += self.parent.y
				self.x += self.parent.x

class DisplayableContainer(Displayable):
	"""
	DisplayableContainers are Displayables which contain other Displayables.

	This is also an abstract class. The methods draw, poke, finalize,
	click, press and destroy are overridden here and will recursively
	call the function on all contained objects.

	New methods:

	add_child(object) -- add the object to the container.
	remove_child(object) -- remove the object from the container.

	New attributes:

	container -- a list with all contained objects (rw)
	"""

	def __init__(self, win, env=None, fm=None, settings=None):
		if env is not None:
			self.env = env
		if fm is not None:
			self.fm = fm
		if settings is not None:
			self.settings = settings

		self.container = []

		Displayable.__init__(self, win)
	
	# ----------------------------------------------- overrides

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

	def press(self, key):
		"""Recursively called on objects in container"""
		focused_obj = self._get_focused_obj()

		if focused_obj:
			focused_obj.press(key)
			return True
		return False

	def click(self, event):
		"""Recursively called on objects in container"""
		focused_obj = self._get_focused_obj()
		if focused_obj and focused_obj.click(event):
			return True

		for displayable in self.container:
			if event in displayable:
				if displayable.click(event):
					return True

		return False

	def destroy(self):
		"""Recursively called on objects in container"""
		for displayable in self.container:
			displayable.destroy()

	# ----------------------------------------------- new methods

	def add_child(self, obj):
		"""Add the objects to the container."""
		if obj.parent:
			obj.parent.remove_child(obj)
		self.container.append(obj)
		obj.parent = self
	
	def remove_child(self, obj):
		"""Remove the object from the container."""
		try:
			container.remove(obj)
		except ValueError:
			pass
		else:
			obj.parent = None
	
	def _get_focused_obj(self):
		# Finds a focused displayable object in the container.
		for displayable in self.container:
			if displayable.focused:
				return displayable
			try:
				obj = displayable._get_focused_obj()
			except AttributeError:
				pass
			else:
				if obj is not None:
					return obj
		return None

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
