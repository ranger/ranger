# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import socket
import sys
import curses
import _curses

from .displayable import DisplayableContainer
from ranger.container.keymap import CommandArgs
from .mouse_event import MouseEvent

TERMINALS_WITH_TITLE = ("xterm", "xterm-256color", "rxvt",
		"rxvt-256color", "rxvt-unicode", "aterm", "Eterm",
		"screen", "screen-256color")

MOUSEMASK = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION

def _setup_mouse(signal):
	if signal['value']:
		curses.mousemask(MOUSEMASK)
		curses.mouseinterval(0)

		## this line solves this problem:
		## If an action, following a mouse click, includes the
		## suspension and re-initializion of the ui (e.g. running a
		## file by clicking on its preview) and the next key is another
		## mouse click, the bstate of this mouse event will be invalid.
		## (atm, invalid bstates are recognized as scroll-down)
		curses.ungetmouse(0,0,0,0,0)
	else:
		curses.mousemask(0)

class UI(DisplayableContainer):
	is_set_up = False
	load_mode = False
	def __init__(self, env=None, fm=None):
		self._draw_title = os.environ["TERM"] in TERMINALS_WITH_TITLE
		os.environ['ESCDELAY'] = '25'   # don't know a cleaner way

		if env is not None:
			self.env = env
		if fm is not None:
			self.fm = fm

		self.win = curses.initscr()
		self.env.keymanager.use_context('browser')
		self.env.keybuffer.clear()

		DisplayableContainer.__init__(self, None)

	def initialize(self):
		"""initialize curses, then call setup (at the first time) and resize."""
		self.win.leaveok(0)
		self.win.keypad(1)
		self.load_mode = False

		curses.cbreak()
		curses.noecho()
		curses.halfdelay(20)
		try:
			curses.curs_set(int(bool(self.settings.show_cursor)))
		except:
			pass
		curses.start_color()
		curses.use_default_colors()

		self.settings.signal_bind('setopt.mouse_enabled', _setup_mouse)
		_setup_mouse(dict(value=self.settings.mouse_enabled))

		if not self.is_set_up:
			self.is_set_up = True
			self.setup()
		self.update_size()

	def suspend(self):
		"""Turn off curses"""
		self.win.keypad(0)
		curses.nocbreak()
		curses.echo()
		try:
			curses.curs_set(1)
		except:
			pass
		if self.settings.mouse_enabled:
			_setup_mouse(dict(value=False))
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
		self.suspend()
		DisplayableContainer.destroy(self)

	def handle_mouse(self):
		"""Handles mouse input"""
		try:
			event = MouseEvent(curses.getmouse())
		except _curses.error:
			return

		DisplayableContainer.click(self, event)

	def handle_key(self, key):
		"""Handles key input"""

		if hasattr(self, 'hint'):
			self.hint()

		if key < 0:
			self.env.keybuffer.clear()
			return

		if DisplayableContainer.press(self, key):
			return

		self.env.keymanager.use_context('browser')
		self.env.key_append(key)
		kbuf = self.env.keybuffer
		cmd = kbuf.command

		self.fm.hide_bookmarks()

		if kbuf.failure:
			kbuf.clear()
			return
		elif not cmd:
			return

		self.env.cmd = cmd

		if cmd.function:
			try:
				cmd.function(CommandArgs.from_widget(self.fm))
			except Exception as error:
				self.fm.notify(error)
			if kbuf.done:
				kbuf.clear()
		else:
			kbuf.clear()

	def handle_keys(self, *keys):
		for key in keys:
			self.handle_key(key)

	def handle_input(self):
		key = self.win.getch()
		if key is 27 or key >= 128 and key < 256:
			# Handle special keys like ALT+X or unicode here:
			keys = [key]
			previous_load_mode = self.load_mode
			self.set_load_mode(True)
			for n in range(4):
				getkey = self.win.getch()
				if getkey is not -1:
					keys.append(getkey)
			if len(keys) == 1:
				keys.append(-1)
			if self.settings.xterm_alt_key:
				if len(keys) == 2 and keys[1] in range(127, 256):
					keys = [27, keys[1] - 128]
			self.handle_keys(*keys)
			self.set_load_mode(previous_load_mode)
			if self.settings.flushinput:
				curses.flushinp()
		else:
			# Handle simple key presses, CTRL+X, etc here:
			if key > 0:
				if self.settings.flushinput:
					curses.flushinp()
				if key == curses.KEY_MOUSE:
					self.handle_mouse()
				elif key == curses.KEY_RESIZE:
					self.update_size()
				else:
					if not self.fm.input_is_blocked():
						self.handle_key(key)

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
		"""Draw all objects in the container"""
		self.win.touchwin()
		DisplayableContainer.draw(self)
		if self._draw_title and self.settings.update_title:
			cwd = self.fm.env.cwd.path
			if cwd.startswith(self.env.home_path):
				cwd = '~' + cwd[len(self.env.home_path):]
			if self.settings.shorten_title:
				split = cwd.rsplit(os.sep, self.settings.shorten_title)
				if os.sep in split[0]:
					cwd = os.sep.join(split[1:])
			sys.stdout.write("\033]2;ranger:" + cwd + "\007")
		self.win.refresh()

	def finalize(self):
		"""Finalize every object in container and refresh the window"""
		DisplayableContainer.finalize(self)
		self.win.refresh()
