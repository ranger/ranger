
RATIO = ( 3, 3, 12, 9 )

from ranger.gui.ui import UI
class DefaultUI(UI):
	def setup(self):
		"""Build up the UI by initializing widgets."""
		from ranger.gui.widgets.filelistcontainer import FileListContainer
		from ranger.gui.widgets.titlebar import TitleBar
		from ranger.gui.widgets.console import Console
		self.titlebar = TitleBar(self.win)
		self.add_obj(self.titlebar)

		self.filelist_container = FileListContainer(self.win, RATIO)
		self.add_obj(self.filelist_container)
		self.main_filelist = self.filelist_container.main_filelist

		self.console = Console(self.win)
		self.add_obj(self.console)

	def update_size(self):
		"""resize all widgets"""
		UI.update_size(self)
		y, x = self.env.termsize

		self.filelist_container.resize(1, 0, y-2, x)
		self.titlebar.resize(0, 0, 1, x)
		self.console.resize(y-1, 0, 1, x)

	def open_console(self, mode):
		if self.console.open(mode):
			self.console.on_close = self.close_console
			self.console.visible = True

	def close_console(self):
		self.console.visible = False

	def scroll(self, relative):
		if self.main_filelist:
			self.main_filelist.scroll(relative)
