
RATIO = ( 3, 3, 12, 9 )

from ranger.gui.ui import UI
class DefaultUI(UI):
	def setup(self):
		"""Build up the UI by initializing widgets."""
		from ranger.gui.widgets.browserview import BrowserView
		from ranger.gui.widgets.titlebar import TitleBar
		from ranger.gui.widgets.console import Console
		from ranger.gui.widgets.statusbar import StatusBar
		from ranger.gui.widgets.process_manager import ProcessManager
		from ranger.gui.widgets.notify import Notify
		from ranger.gui.widgets.pager import Pager

		# Create a title bar
		self.titlebar = TitleBar(self.win)
		self.add_child(self.titlebar)

		# Create the browser view
		self.browser = BrowserView(self.win, RATIO)
		self.add_child(self.browser)
		self.main_column = self.browser.main_column

		# Create the process manager
		self.pman = ProcessManager(self.win)
		self.pman.visible = False
		self.add_child(self.pman)

		# Create the (initially hidden) notify bar
		self.notify = Notify(self.win)
		self.add_child(self.notify)

		# Create the status bar
		self.status = StatusBar(self.win, self.browser.main_column)
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

		self.browser.resize(1, 0, y - 1 - notify_hei, x)
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
		self.browser.visible = True
	
	def open_pager(self):
		if self.console.focused:
			self.console.focused = False
		self.pager.visible = True
		self.pager.focused = True
		self.browser.visible = False
		return self.pager

	def open_embedded_pager(self):
		self.browser.open_pager()
		return self.browser.pager

	def close_embedded_pager(self):
		self.browser.close_pager()
	
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
		self.browser.visible = False
		self.pman.visible = True
		self.pman.focused = True

	def close_pman(self):
		self.pman.visible = False
		self.browser.visible = True
		self.pman.focused = False

	def scroll(self, relative):
		if self.browser and self.browser.main_column:
			self.browser.main_column.scroll(relative)
	
	def throbber(self, string='.', remove=False):
		if remove:
			self.titlebar.throbber = type(self.titlebar).throbber
		else:
			self.titlebar.throbber = string
	
#		self.win.addnstr(0, self.env.termsize[1]-1, string, 1)

	def hint(self, text=None):
		self.status.override = text
