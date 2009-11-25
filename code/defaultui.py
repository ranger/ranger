import ui
import widget, wdisplay

class DefaultUI(ui.UI):
	def setup(self):
		self.main_display = wdisplay.WDisplay(self.win, 0)
		self.add_widget(self.main_display)
		self.left_display = wdisplay.WDisplay(self.win, -1)
		self.add_widget(self.left_display)
	
	def resize(self):
		ui.UI.resize(self)
		y, x = self.win.getmaxyx()
		self.main_display.setdim(1, 40, 3, 37)
		self.left_display.setdim(1, 0, 3, 37)

