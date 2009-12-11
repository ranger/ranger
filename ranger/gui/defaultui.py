
RATIO = ( 0.15, 0.15, 0.4, 0.3 )

from ranger.gui.ui import UI as SuperClass
class DefaultUI(SuperClass):
	def setup(self):
		from ranger.gui.widgets.filelist import FileList
		from ranger.gui.widgets.titlebar import TitleBar
		from ranger.gui.widgets.console import Console
		self.titlebar = TitleBar(self.win)
		self.add_obj(self.titlebar)

		self.displays = [
				FileList(self.win, -2),
				FileList(self.win, -1),
				FileList(self.win, 0),
				FileList(self.win, 1) ]
		self.main_display = self.displays[2]
		self.displays[2].display_infostring = True
		self.displays[2].main_display = True
		for disp in self.displays:
			self.add_obj(disp)

		self.console = Console(self.win)
		self.add_obj(self.console)

	def update_size(self):
		"""resize all widgets"""
		SuperClass.update_size(self)
		y, x = self.win.getmaxyx()

		leftborder = 0

		i = 0
		for ratio in RATIO:
			wid = int(ratio * x)
			try:
				self.displays[i].resize(1, leftborder, y-2, wid - 1)
			except KeyError:
				pass
			leftborder += wid
			i += 1

		self.titlebar.resize(0, 0, 1, x)
		self.console.resize(y-1, 0, 1, x)

	def open_console(self, mode):
		if self.console.open(mode):
			self.console.on_close = self.close_console
			self.console.visible = True

	def close_console(self):
		self.console.visible = False

	def scroll(self, relative):
		self.main_display.scroll(relative)

