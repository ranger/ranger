
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
		from ranger.gui.widgets.process_manager import ProcessManager
		from ranger.gui.widgets.notify import Notify
		from ranger.gui.widgets.pager import Pager

		self.titlebar = TitleBar(self.win)
		self.add_obj(self.titlebar)

		self.filelist_container = FileListContainer(self.win, RATIO)
		self.add_obj(self.filelist_container)
		self.main_filelist = self.filelist_container.main_filelist

		self.pman = ProcessManager(self.win)
		self.pman.visible = False
		self.add_obj(self.pman)

		self.notify = Notify(self.win)
		self.add_obj(self.notify)

		self.status = StatusBar(self.win, self.main_filelist)
		self.add_obj(self.status)
		self.console = Console(self.win)
		self.add_obj(self.console)
		self.console.visible = False

		self.pager = Pager(self.win)
		self.add_obj(self.pager)

	def update_size(self):
		"""resize all widgets"""
		UI.update_size(self)
		y, x = self.env.termsize

		notify_hei = min(max(1, y - 4), self.notify.requested_height)

		self.filelist_container.resize(1, 0, y - 1 - notify_hei, x)
		self.pman.resize(1, 0, y - 1 - notify_hei, x)
		self.pager.resize(1, 0, y - 1 - notify_hei, x)
		self.notify.resize(y - notify_hei, 0, notify_hei, x)
		self.titlebar.resize(0, 0, 1, x)
		self.status.resize(y - 1, 0, 1, x)
		self.console.resize(y - 1, 0, 1, x)
	
	def poke(self):
		UI.poke(self)
		if self.notify.requested_height != self.notify.hei:
			self.update_size()
	
	def display(self, *a, **k):
		return self.notify.display(*a, **k)

	def close_pager(self):
		self.pager.visible = False
		self.pager.focused = False
		self.filelist_container.visible = True
	
	def open_pager(self):
		self.pager.visible = True
		self.pager.focused = True
		self.filelist_container.visible = False

	def open_embedded_pager(self):
		self.filelist_container.open_pager()
		return self.filelist_container.pager

	def close_embedded_pager(self):
		self.filelist_container.close_pager()
	
	def open_console(self, mode, string=''):
		if self.console.open(mode, string):
			self.console.on_close = self.close_console
			self.console.visible = True
			self.status.visible = False

	def close_console(self):
		self.console.visible = False
		self.status.visible = True

	def open_pman(self):
		self.filelist_container.visible = False
		self.pman.visible = True
		self.pman.focused = True

	def close_pman(self):
		self.pman.visible = False
		self.filelist_container.visible = True
		self.pman.focused = False

	def scroll(self, relative):
		if self.main_filelist:
			self.main_filelist.scroll(relative)
	
	def throbber(self, string='.', remove=False):
		if remove:
			self.titlebar.throbber = type(self.titlebar).throbber
		else:
			self.titlebar.throbber = string
	
#		self.win.addnstr(0, self.env.termsize[1]-1, string, 1)

	def hint(self, text=None):
		self.status.override = text
