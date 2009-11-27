import ranger.ui
from ranger.wdisplay import WDisplay
from ranger.wstatusbar import WStatusBar

class DefaultUI(ranger.ui.UI):
	def setup(self):
		self.statusbar = WStatusBar(self.win)
		self.add_widget(self.statusbar)

		self.displays = [
				WDisplay(self.win, -2),
				WDisplay(self.win, -1),
				WDisplay(self.win, 0),
				WDisplay(self.win, 1) ]
		self.displays[2].display_infostring = True
		self.displays[2].main_display = True
		for disp in self.displays:
			self.add_widget(disp)
	
	RATIO = ( 0.15, 0.15, 0.4, 0.3 )
	
	def resize(self):
		ranger.ui.UI.resize(self)
		y, x = self.win.getmaxyx()

		leftborder = 0

		i = 0
		for ratio in DefaultUI.RATIO:
			wid = int(ratio * x)
			try:
				self.displays[i].setdim(1, leftborder, y-1, wid - 1)
			except KeyError:
				pass
			leftborder += wid
			i += 1

		self.statusbar.setdim(0, 0, 1, x)

