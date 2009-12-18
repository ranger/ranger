
RATIO = ( 3, 3, 12, 9 )
from ranger import log

from ranger.gui.ui import UI
class DefaultUI(UI):
	def setup(self):
		"""Build up the UI by initializing widgets."""
		from ranger.gui.widgets.filelistcontainer import FileListContainer
		from ranger.gui.widgets.titlebar import TitleBar
		from ranger.gui.widgets.console import Console
		from ranger.gui.widgets.statusbar import StatusBar
		from ranger.gui.widgets.notify import Notify
		self.titlebar = TitleBar(self.win)
		self.add_obj(self.titlebar)

		self.filelist_container = FileListContainer(self.win, RATIO)
		self.add_obj(self.filelist_container)
		self.main_filelist = self.filelist_container.main_filelist

		self.status = StatusBar(self.win, self.main_filelist)
		self.add_obj(self.status)
		self.console = Console(self.win)
		self.add_obj(self.console)
		self.console.visible = False

		self.notify = Notify(self.win)
		self.add_obj(self.notify)

	def update_size(self):
		"""resize all widgets"""
		UI.update_size(self)
		y, x = self.env.termsize

		notify_hei = self.notify.requested_height
		log(notify_hei)

		self.filelist_container.resize(1, 0, y - 2 - notify_hei, x)
		self.notify.resize(y - 1 - notify_hei, 0, notify_hei, x)
		self.titlebar.resize(0, 0, 1, x)
		self.status.resize(y - 1, 0, 1, x)
		self.console.resize(y - 1, 0, 1, x)
	
	def poke(self):
		UI.poke(self)
		if self.notify.requested_height != self.notify.hei:
			self.update_size()
	
	def display(self, *a, **k):
		return self.notify.display(*a, **k)

	def open_console(self, mode, string=''):
		if self.console.open(mode, string):
			self.console.on_close = self.close_console
			self.console.visible = True
			self.status.visible = False

	def close_console(self):
		self.console.visible = False
		self.status.visible = True

	def scroll(self, relative):
		if self.main_filelist:
			self.main_filelist.scroll(relative)
