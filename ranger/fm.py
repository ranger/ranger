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

from time import time
from collections import deque

from ranger.actions import Actions
from ranger.container import Bookmarks
from ranger.ext.relpath import relpath_conf
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
		self.apps = self.settings.apps.CustomApplications()

		from ranger.shared import FileManagerAware
		FileManagerAware.fm = self

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
				try:
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

				except KeyboardInterrupt:
					self.ui.handle_key(CTRL_C)
		finally:
			self.bookmarks.remember(self.env.pwd)
			self.bookmarks.save()
