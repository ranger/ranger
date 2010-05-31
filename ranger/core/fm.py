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

"""
The File Manager, putting the pieces together
"""

from time import time
from collections import deque
from select import select, error as SelectError
from struct import Struct
import os
import sys

import ranger
from ranger.core.actions import Actions
from ranger.container.tags import Tags
from ranger.gui.defaultui import DefaultUI
from ranger.container import Bookmarks
from ranger.core.runner import Runner
from ranger import relpath_conf
from ranger.ext.get_executables import get_executables
from ranger.fsobject import Directory
from ranger.ext.signal_dispatcher import SignalDispatcher
from ranger import __version__
from ranger.core.loader import Loader

CTRL_C = 3

class FM(Actions, SignalDispatcher):
	input_blocked = False
	input_blocked_until = 0
	def __init__(self, ui=None, bookmarks=None, tags=None):
		"""Initialize FM."""
		Actions.__init__(self)
		SignalDispatcher.__init__(self)
		self.ui = ui
		self.log = deque(maxlen=20)
		self.bookmarks = bookmarks
		self.tags = tags
		self.tabs = {}
		self.current_tab = 1
		self.loader = Loader()

		self.log.append('Ranger {0} started! Process ID is {1}.' \
				.format(__version__, os.getpid()))
		self.log.append('Running on Python ' + sys.version.replace('\n',''))

	# COMPAT
	@property
	def executables(self):
		"""For compatibility. Calls get_executables()"""
		return get_executables()

	def initialize(self):
		"""If ui/bookmarks are None, they will be initialized here."""
		if self.bookmarks is None:
			if ranger.arg.clean:
				bookmarkfile = None
			else:
				bookmarkfile = relpath_conf('bookmarks')
			self.bookmarks = Bookmarks(
					bookmarkfile=bookmarkfile,
					bookmarktype=Directory,
					autosave=self.settings.autosave_bookmarks)
			self.bookmarks.load()

		else:
			self.bookmarks = bookmarks

		if not ranger.arg.clean and self.tags is None:
			self.tags = Tags(relpath_conf('tagged'))

		if self.ui is None:
			self.ui = DefaultUI()
			self.ui.initialize()

		def mylogfunc(text):
			self.notify(text, bad=True)
		self.run = Runner(ui=self.ui, apps=self.apps,
				logfunc=mylogfunc)

		self.env.signal_bind('cd', self._update_current_tab)

	def block_input(self, sec=0):
		self.input_blocked = sec != 0
		self.input_blocked_until = time() + sec

	def input_is_blocked(self):
		if self.input_blocked and time() > self.input_blocked_until:
			self.input_blocked = False
		return self.input_blocked

	def loop(self):
		"""
		The main loop consists of:
		1. reloading bookmarks if outdated
		2. letting the loader work
		3. drawing and finalizing ui
		4. reading and handling user input
		"""

		self.env.enter_dir(self.env.path)

		gc_tick = 0

		# for faster lookup:
		ui = self.ui
		throbber = ui.throbber
		bookmarks = self.bookmarks
		loader = self.loader
		env = self.env
		watches = env.map_watch_to_dir
		stdin = sys.stdin
		wait_handles = env.wait_handles
		event_struct = Struct('i3I')
		has_throbber = hasattr(ui, 'throbber')

		try:
			while True:
				bookmarks.update_if_outdated()
				loader.work()
				if has_throbber:
					if loader.has_work():
						throbber(loader.status)
					else:
						throbber(remove=True)

				ui.redraw()

				ui.set_load_mode(loader.has_work())

				try:
					ready_handles = select(wait_handles, (), (), 0 if loader.has_work() else None)[0]
				except SelectError:
					pass # (Interrupted system call, due to resize or ^C)

				for handle in ready_handles:
					if handle == stdin:
						ui.handle_input()
					else:
						# If we reach this, we have new inotify events that need to be processed
						event_buffer = handle.read(event_struct.size)
						watch, events, cookie, filename_len = event_struct.unpack(event_buffer)
						if not events & 0x0000C000: # IN_IGNORED | IN_Q_OVERFLOW
							if filename_len > 0:
								filename = handle.read(filename_len).strip('\x00').decode()
							else:
								filename = ''
							watches[watch].handle_changes(events, filename)

		except KeyboardInterrupt:
			# this only happens in --debug mode. By default, interrupts
			# are caught in curses_interrupt_handler
			raise SystemExit

		finally:
			bookmarks.remember(env.cwd)
			bookmarks.save()
