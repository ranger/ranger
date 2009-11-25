import widget
import curses
import file, directory

class WDisplay(widget.Widget):
	def __init__(self, win, level):
		widget.Widget.__init__(self,win)
		self.level = level

	def feed_env(self, env):
		self.target = env.at_level(self.level)

	def draw(self):
		if type(self.target) == file.File:
			self.draw_file()
		elif type(self.target) == directory.Directory:
			self.draw_directory()
		elif self.target is None:
			self.win.addnstr(self.y, self.x, "---", self.wid)
		else:
			self.win.addnstr(self.y, self.x, "unknown type.", self.wid)

	def draw_file(self):
		self.win.addnstr(self.y, self.x, "this is a file.", self.wid)

	def draw_directory(self):
		self.target.load_content_once()
		for i in range(self.hei):
			try:
				f = self.target[i]
			except IndexError:
				break
			self.win.addnstr(self.y + i, self.x, self.target[i].path, self.wid)

