import curses
from ranger.debug import log
class UI():
	def __init__(self, env, commandlist):
		self.env = env
		self.commandlist = commandlist

		self.widgets = []
		self.win = curses.initscr()
		self.win.leaveok(1)

		self.initialize()

		self.setup()
		self.resize()

	def initialize(self):
		curses.noecho()
		curses.halfdelay(10)
		curses.curs_set(0)

	def setup(self):
		pass

	def resize(self):
		self.env.termsize = self.win.getmaxyx()

	def redraw(self):
		self.win.redrawwin()
		self.win.refresh()
		self.win.redrawwin()

	def add_widget(self, widg):
		self.widgets.append(widg)

	def feed_env(self, env):
		self.env = env

	def press(self, key, fm):
		self.env.key_append(key)
		log(self.env.keybuffer)

		try:
			cmd = self.commandlist.paths[self.env.keybuffer]
		except KeyError:
			self.env.key_clear()
			return

		if cmd == self.commandlist.dummy_object:
			return

		cmd.execute(fm)
		self.env.key_clear()

	def exit(self):
		curses.nocbreak()
		curses.echo()
		curses.endwin()

	def draw(self):
		from ranger.debug import log
		self.win.erase()
		for widg in self.widgets:
			widg.feed_env(self.env)
			widg.draw()
		self.win.refresh()

	def get_next_key(self):
		key = self.win.getch()
		curses.flushinp()
		return key

