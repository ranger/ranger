from ranger.actions import Actions
from ranger.container import Bookmarks
from ranger import __version__

CTRL_C = 3
TICKS_BEFORE_COLLECTING_GARBAGE = 100

class FM(Actions):
	def __init__(self, ui = None, bookmarks = None):
		"""Initialize FM."""
		Actions.__init__(self)
		self.ui = ui
		self.bookmarks = bookmarks
		self.apps = self.settings.apps.CustomApplications()

		from ranger.shared import FileManagerAware
		FileManagerAware.fm = self

	def initialize(self):
		"""If ui/bookmarks are None, they will be initialized here."""

		if self.bookmarks is None:
			self.bookmarks = Bookmarks()
			self.bookmarks.load()

		else:
			self.bookmarks = bookmarks
		self.bookmarks.enter_dir_function = self.enter_dir

		if self.ui is None:
			from ranger.gui.defaultui import DefaultUI
			self.ui = DefaultUI()
			self.ui.initialize()

	def loop(self):
		"""The main loop consists of:
1. reloading bookmarks if outdated
2. drawing and finalizing ui
3. reading and handling user input
4. after X loops: collecting unused directory objects"""

		self.env.enter_dir(self.env.path)

		gc_tick = 0

		while True:
			try:
				self.bookmarks.reload_if_outdated()
				self.ui.draw()
				self.ui.finalize()

				key = self.ui.get_next_key()
				self.ui.handle_key(key)

				gc_tick += 1
				if gc_tick > TICKS_BEFORE_COLLECTING_GARBAGE:
					gc_tick = 0
					self.env.garbage_collect()

			except KeyboardInterrupt:
				self.ui.handle_key(CTRL_C)
