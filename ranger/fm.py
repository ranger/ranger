from ranger.actions import Actions
from ranger.container import Bookmarks
from ranger import __version__

USAGE = '''%s [options] [path/filename]'''

class FM(Actions):
	def __init__(self, ui = None, bookmarks = None):
		Actions.__init__(self)
		self.ui = ui
		self.apps = self.settings.apps.CustomApplications()

		if bookmarks is None:
			self.bookmarks = Bookmarks()
			self.bookmarks.load()

		else:
			self.bookmarks = bookmarks
		self.bookmarks.enter_dir_function = self.enter_dir

		from ranger.shared import FileManagerAware
		FileManagerAware.fm = self

	def loop(self):
		if self.ui is None:
			from ranger.gui.defaultui import DefaultUI
			self.ui = DefaultUI()
			self.ui.initialize()

		self.env.enter_dir(self.env.path)

		gc_tick = 0

		while True:
			try:
				self.bookmarks.reload_if_outdated()
				self.ui.draw()
				key = self.ui.get_next_key()
				self.ui.press(key, self)

				gc_tick += 1
				if gc_tick > 10:
					gc_tick = 0
					self.env.garbage_collect()

			except KeyboardInterrupt:
				self.ui.press(3, self)
