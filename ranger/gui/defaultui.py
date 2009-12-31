
RATIO = ( 3, 3, 12, 9 )

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

		# Create a title bar
		self.titlebar = TitleBar(self.win)
		self.add_child(self.titlebar)

		# Create the container for the filelists
		self.filelist_container = FileListContainer(self.win, RATIO)
		self.add_child(self.filelist_container)
		self.main_filelist = self.filelist_container.main_filelist

		# Create the process manager
		self.pman = ProcessManager(self.win)
		self.pman.visible = False
		self.add_child(self.pman)

		# Create the (initially hidden) notify bar
		self.notify = Notify(self.win)
		self.add_child(self.notify)

		# Create the status bar
		self.status = StatusBar(self.win, self.main_filelist)
		self.add_child(self.status)

		# Create the console
		self.console = Console(self.win)
		self.add_child(self.console)
		self.console.visible = False

		# Create the pager
		self.pager = Pager(self.win)
		self.add_child(self.pager)

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
		if self.console.visible:
			self.console.focused = True
		self.pager.visible = False
		self.pager.focused = False
		self.filelist_container.visible = True
	
	def open_pager(self):
		if self.console.focused:
			self.console.focused = False
		self.pager.visible = True
		self.pager.focused = True
		self.filelist_container.visible = False
		return self.pager

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
		self.close_pager()

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
