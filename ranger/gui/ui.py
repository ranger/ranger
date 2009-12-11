import curses

from .displayable import DisplayableContainer
from .mouse_event import MouseEvent
from ranger.container import CommandList

class UI(DisplayableContainer):
	is_set_up = False
	def __init__(self, commandlist = None):
		import os
		os.environ['ESCDELAY'] = '25' # don't know a cleaner way

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

		curses.cbreak()
		curses.noecho()
		curses.halfdelay(20)
		curses.curs_set(0)
		curses.start_color()
		curses.use_default_colors()

		curses.mouseinterval(0)
		mask = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION
		avail, old = curses.mousemask(mask)
		curses.mousemask(avail)

		if not self.is_set_up:
			self.is_set_up = True
			self.setup()
		self.update_size()

	def handle_mouse(self):
		"""Handles mouse input"""
		try:
			event = MouseEvent(curses.getmouse())
		except:
			return

		from ranger import log
		log(str(event.bstate))

		if event.pressed(1) or event.pressed(3):
			for displayable in self.container:
				if displayable.contains_point(event.y, event.x):
					displayable.click(event)
					break

#		if event.pressed(4) or event.pressed(2) or event.bstate & 134217728:
		if event.pressed(4) or event.pressed(2):
			if event.pressed(4):
				self.fm.scroll(relative = -3)
			else:
				self.fm.scroll(relative = 3)

	def handle_key(self, key):
		"""Handles key input"""
		self.env.key_append(key)

		if DisplayableContainer.press(self, key):
			return

		try:
			cmd = self.commandlist.paths[tuple(self.env.keybuffer)]
		except KeyError:
			self.env.key_clear()
			return

		if cmd == self.commandlist.dummy_object:
			return

		cmd.execute(self.fm)
		self.env.key_clear()

	def get_next_key(self):
		"""Waits for key input and returns the pressed key"""
		key = self.win.getch()
		curses.flushinp()
		return key

	def setup(self):
		"""Called after an initialize() call.
Override this!"""

	def redraw(self):
		"""Redraw the window. This only calls self.win.redrawwin()."""
		self.win.redrawwin()
		self.win.refresh()
		self.win.redrawwin()

	def update_size(self):
		"""Update self.env.termsize.
Extend this method to resize all widgets!"""
		self.env.termsize = self.win.getmaxyx()

	def draw(self):
		"""Erase the window, then draw all objects in the container"""
		self.win.erase()
		DisplayableContainer.draw(self)

	def finalize(self):
		"""Finalize every object in container and refresh the window"""
		DisplayableContainer.finalize(self)
		self.win.refresh()

	def destroy(self):
		"""Destroy all widgets and turn off curses"""
#		DisplayableContainer.destroy(self)
		from ranger import log
		log("exiting ui!")
		self.win.keypad(0)
		curses.nocbreak()
		curses.echo()
		curses.curs_set(1)
#		curses.mousemask(0)
		curses.endwin()
