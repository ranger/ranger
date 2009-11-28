import curses
from ranger.gui.widget import Widget as SuperClass

class WTitleBar(SuperClass):
	def feed_env(self, env):
		self.pathway = env.pathway

	def draw(self):
		self.win.move(self.y, self.x)
		for path in self.pathway:
			currentx = self.win.getyx()[1]
			self.win.addnstr(path.basename + ' / ', (self.wid - currentx))
