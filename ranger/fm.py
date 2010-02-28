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

from time import time
from collections import deque

from ranger.actions import Actions
from ranger.container import Bookmarks
from ranger.runner import Runner
from ranger.ext.relpath import relpath_conf
from ranger.ext.get_executables import get_executables
from ranger import __version__
from ranger.fsobject import Loader

CTRL_C = 3
TICKS_BEFORE_COLLECTING_GARBAGE = 100

class FM(Actions):
	input_blocked = False
	input_blocked_until = 0
	stderr_to_out = False
	def __init__(self, ui=None, bookmarks=None, tags=None):
		"""Initialize FM."""
		Actions.__init__(self)
		self.ui = ui
		self.log = deque(maxlen=20)
		self.bookmarks = bookmarks
		self.tags = tags
		self.loader = Loader()
		self._executables = None
		self.apps = self.settings.apps.CustomApplications()

		def mylogfunc(text):
			self.notify(text, bad=True)
		self.run = Runner(ui=self.ui, apps=self.apps,
				logfunc=mylogfunc)

		from ranger.shared import FileManagerAware
		FileManagerAware.fm = self

	@property
	def executables(self):
		if self._executables is None:
			self._executables = sorted(get_executables())
		return self._executables

	def initialize(self):
		"""If ui/bookmarks are None, they will be initialized here."""
		from ranger.fsobject.directory import Directory

		if self.bookmarks is None:
			self.bookmarks = Bookmarks(
					bookmarkfile=relpath_conf('bookmarks'),
					bookmarktype=Directory,
					autosave=self.settings.autosave_bookmarks)
			self.bookmarks.load()

		else:
			self.bookmarks = bookmarks

		from ranger.container.tags import Tags
		if self.tags is None:
			self.tags = Tags('~/.ranger/tagged')

		if self.ui is None:
			from ranger.gui.defaultui import DefaultUI
			self.ui = DefaultUI()
			self.ui.initialize()

	def block_input(self, sec=0):
		self.input_blocked = sec != 0
		self.input_blocked_until = time() + sec

	def loop(self):
		"""
		The main loop consists of:
		1. reloading bookmarks if outdated
		2. letting the loader work
		3. drawing and finalizing ui
		4. reading and handling user input
		5. after X loops: collecting unused directory objects
		"""

		self.env.enter_dir(self.env.path)

		gc_tick = 0

		try:
			while True:
				self.bookmarks.update_if_outdated()
				self.loader.work()
				if hasattr(self.ui, 'throbber'):
					if self.loader.has_work():
						self.ui.throbber(self.loader.status)
					else:
						self.ui.throbber(remove=True)

				self.ui.redraw()

				self.ui.set_load_mode(self.loader.has_work())

				key = self.ui.get_next_key()

				if key > 0:
					if self.input_blocked and \
							time() > self.input_blocked_until:
						self.input_blocked = False
					if not self.input_blocked:
						self.ui.handle_key(key)

				gc_tick += 1
				if gc_tick > TICKS_BEFORE_COLLECTING_GARBAGE:
					gc_tick = 0
					self.env.garbage_collect()

		finally:
			self.bookmarks.remember(self.env.pwd)
			self.bookmarks.save()
