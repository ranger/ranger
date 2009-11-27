import ranger.widget
import curses

class WDisplay(ranger.widget.Widget):
	def __init__(self, win, level):
		ranger.widget.Widget.__init__(self,win)
		self.level = level
		self.main_display = False
		self.display_infostring = False

	def feed_env(self, env):
		self.target = env.at_level(self.level)

	def draw(self):
		from ranger.file import File
		from ranger.directory import Directory

		if self.target is None:
			pass
		elif type(self.target) == File:
			self.draw_file()
		elif type(self.target) == Directory:
			self.draw_directory()
		else:
			self.win.addnstr(self.y, self.x, "unknown type.", self.wid)

	def draw_file(self):
		if not self.target.accessible:
			self.win.addnstr(self.y, self.x, "not accessible", self.wid)
			return
		self.win.addnstr(self.y, self.x, "this is a file.", self.wid)

	def draw_directory(self):
		self.target.load_content_once()
		main_display = self.main_display
		if not self.target.accessible:
			self.win.addnstr(self.y, self.x, "not accessible", self.wid)
			return
		for i in range(self.hei):
			try:
				drawed = self.target[i]
			except IndexError:
				break
			invert = main_display and i == self.target.pointed_index
			if invert:
				self.win.attrset(curses.A_REVERSE)
			self.win.addnstr(self.y + i, self.x, drawed.basename, self.wid)
			if self.display_infostring and drawed.infostring:
				info = drawed.infostring
				x = self.x + self.wid - 1 - len(info)
				if x > self.x:
					self.win.addstr(self.y + i, x, str(info) + '')
			if invert:
				self.win.attrset(curses.A_NORMAL)


