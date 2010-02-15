# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import socket
import sys
import curses
import _curses

from .displayable import DisplayableContainer
from .mouse_event import MouseEvent
from ranger.container import CommandList

class UI(DisplayableContainer):
	is_set_up = False
	mousemask = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION
	load_mode = False
	def __init__(self, commandlist=None, env=None, fm=None):
		import os
		os.environ['ESCDELAY'] = '25'   # don't know a cleaner way

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
		curses.curs_set(int(bool(self.settings.show_cursor)))
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
		# from ranger import log
		# log("suspending ui!")
		self.win.keypad(0)
		curses.nocbreak()
		curses.echo()
		curses.curs_set(1)
		curses.mousemask(0)
		curses.endwin()

	def set_load_mode(self, boolean):
		boolean = bool(boolean)
		if boolean != self.load_mode:
			self.load_mode = boolean

			if boolean:
				# don't wait for key presses in the load mode
				curses.cbreak()
				self.win.nodelay(1)
			else:
				self.win.nodelay(0)
				curses.halfdelay(20)

	def destroy(self):
		"""Destroy all widgets and turn off curses"""
		DisplayableContainer.destroy(self)
		self.suspend()

	def handle_mouse(self):
		"""Handles mouse input"""
		try:
			event = MouseEvent(curses.getmouse())
		except _curses.error:
			return

		# from ranger import log
		# log('{0:0>28b} ({0})'.format(event.bstate))
		# log('y: {0}  x: {1}'.format(event.y, event.x))

		DisplayableContainer.click(self, event)

	def handle_key(self, key):
		"""Handles key input"""

		if hasattr(self, 'hint'):
			self.hint()

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

		self.env.cmd = cmd

		if hasattr(cmd, 'show_obj') and hasattr(cmd.show_obj, 'hint'):
			if hasattr(self, 'hint'):
				self.hint(cmd.show_obj.hint)
		elif hasattr(cmd, 'execute'):
			try:
				cmd.execute_wrap(self)
			except Exception as error:
				self.fm.notify(error)
			self.env.key_clear()

	def get_next_key(self):
		"""Waits for key input and returns the pressed key"""
		key = self.win.getch()
		if key is not -1:
			if self.settings.flushinput:
				curses.flushinp()
		return key

	def setup(self):
		"""
		Called after an initialize() call.
		Override this!
		"""

	def redraw(self):
		"""Redraw all widgets"""
		self.poke()
		self.draw()
		self.finalize()

	def redraw_window(self):
		"""Redraw the window. This only calls self.win.redrawwin()."""
		self.win.erase()
		self.win.redrawwin()
		self.win.refresh()
		self.win.redrawwin()
		self.need_redraw = True

	def update_size(self):
		"""
		Update self.env.termsize.
		Extend this method to resize all widgets!
		"""
		self.env.termsize = self.win.getmaxyx()

	def draw(self):
		"""Erase the window, then draw all objects in the container"""
		self.win.touchwin()
		DisplayableContainer.draw(self)
		if self.settings.update_title:
			hostname = str(socket.gethostname())
			try:
				cwd = self.fm.env.pwd.path
			except:
				cwd = ' - ranger'
			sys.stdout.write("\033]2;" + hostname + \
					self.fm.env.pwd.path + "\007")
		self.win.refresh()

	def finalize(self):
		"""Finalize every object in container and refresh the window"""
		DisplayableContainer.finalize(self)
		self.win.refresh()
