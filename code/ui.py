import curses, debug
class UI():
	def __init__(self, env):
		self.env = env

		self.widgets = []
		self.win = curses.initscr()
		self.win.leaveok(1)
		curses.noecho()
		curses.halfdelay(3)

		self.setup()
		self.resize()

	def setup(self):
		pass

	def resize(self):
		self.env.termsize = self.win.getmaxyx()

	def add_widget(self, widg):
		self.widgets.append(widg)

	def feed_env(self, env):
		self.env = env

	def exit(self):
		curses.nocbreak()
		curses.echo()
		curses.endwin()

	def draw(self):
		self.win.erase()
		for widg in self.widgets:
			widg.feed_env(self.env)
			widg.draw()
		self.win.refresh()

#		for i in range(1, len(self.env.pwd)):
#			f = self.env.pwd.files[i]
#			self.win.addstr(i, 0, f.path)
#			if f.infostring: self.win.addstr(i, 50, f.infostring)

	def get_next_key(self):
		key = self.win.getch()
		curses.flushinp()
		return key

