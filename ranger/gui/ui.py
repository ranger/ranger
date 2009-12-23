import curses

from .displayable import DisplayableContainer
from .mouse_event import MouseEvent
from ranger.container import CommandList

class UI(DisplayableContainer):
	is_set_up = False
	mousemask = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION
	load_mode = False
	def __init__(self, commandlist=None, env=None, fm=None):
		import os
		os.environ['ESCDELAY'] = '25' # don't know a cleaner way

		if env is not None:
			self.env = env
		if fm is not None:
			self.fm = fm

		if commandlist is None:
			self.commandlist = CommandList()
			self.settings.keys.initialize_commands(self.commandlist)
		else:
			self.commandlist = commandlist
		self.win = curses.initscr()

		DisplayableContainer.__init__(self, None)

	def initialize(self):
		"""initialize curses, then call setup (at the first time) and resize."""
		self.win.leaveok(0)
		self.win.keypad(1)
		self.load_mode = False

		curses.cbreak()
		curses.noecho()
		curses.halfdelay(20)
		curses.curs_set(0)
		curses.start_color()
		curses.use_default_colors()

		curses.mousemask(self.mousemask)
		curses.mouseinterval(0)
		
		## this line solves this problem:
		## If an action, following a mouse click, includes the
		## suspension and re-initializion of the ui (e.g. running a
		## file by clicking on its preview) and the next key is another
		## mouse click, the bstate of this mouse event will be invalid.
		## (atm, invalid bstates are recognized as scroll-down)
		curses.ungetmouse(0,0,0,0,0)

		if not self.is_set_up:
			self.is_set_up = True
			self.setup()
		self.update_size()

	def suspend(self):
		"""Turn off curses"""
		from ranger import log
		log("suspending ui!")
		self.win.keypad(0)
		curses.nocbreak()
		curses.echo()
		curses.curs_set(1)
		curses.mousemask(0)
		curses.endwin()

	def set_load_mode(self, boolean):
		from ranger import log
		boolean = bool(boolean)
		if boolean != self.load_mode:
			self.load_mode = boolean

			if boolean:
				log('setting halfdelay to 1')
				curses.halfdelay(1)
			else:
				log('setting halfdelay to 20')
				curses.halfdelay(20)

	def destroy(self):
		"""Destroy all widgets and turn off curses"""
		DisplayableContainer.destroy(self)
		self.suspend()

	def handle_mouse(self):
		"""Handles mouse input"""
		try:
			event = MouseEvent(curses.getmouse())
		except:
			return

#		from ranger import log
#		log('{0:0>28b} ({0})'.format(event.bstate))

		if DisplayableContainer.click(self, event):
			return

		n = event.ctrl() and 1 or 3
		if event.pressed(4):
			self.fm.scroll(relative = -n)
		elif event.pressed(2) or event.key_invalid():
			self.fm.scroll(relative = n)

	def handle_key(self, key):
		"""Handles key input"""
		self.env.key_append(key)

		if DisplayableContainer.press(self, key):
			return

		try:
			tup = self.env.keybuffer.tuple_without_numbers()

			if tup:
				cmd = self.commandlist[tup]
			else:
				return
		except KeyError:
			self.env.key_clear()
			return

		if cmd == self.commandlist.dummy_object:
			return

		cmd.execute(self.fm, self.env.keybuffer.number)
		self.env.key_clear()

	def get_next_key(self):
		"""Waits for key input and returns the pressed key"""
		key = self.win.getch()
		curses.flushinp()
		return key

	def setup(self):
		"""Called after an initialize() call.
		Override this!
		"""
	
	def redraw(self):
		"""Redraw all widgets"""
		self.poke()
		self.draw()
		self.finalize()

	def redraw_window(self):
		"""Redraw the window. This only calls self.win.redrawwin()."""
		self.win.redrawwin()
		self.win.refresh()
		self.win.redrawwin()

	def update_size(self):
		"""Update self.env.termsize.
		Extend this method to resize all widgets!
		"""
		self.env.termsize = self.win.getmaxyx()

	def draw(self):
		"""Erase the window, then draw all objects in the container"""
		self.win.erase()
		DisplayableContainer.draw(self)
		self.win.refresh()

	def finalize(self):
		"""Finalize every object in container and refresh the window"""
		DisplayableContainer.finalize(self)
		self.win.refresh()
