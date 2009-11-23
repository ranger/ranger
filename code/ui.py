import curses
class UI():
	def __init__(self, options):
		self.scr = curses.initscr()
		self.scr.leaveok(1)
		curses.noecho()
		curses.halfdelay(3)

		self.options = options
		self.directories = None
		self.pwd = None
		self.cf = None
		self.termsize = None
		self.rows = 0
		self.cols = 0

	def feed(self, directories, pwd, cf, termsize):
		self.directories = directories
		self.pwd = pwd
		self.cf = cf
		self.termsize = termsize
		self.cols = termsize.x
		self.rows = termsize.y

	def exit(self):
		curses.nocbreak()
		curses.echo()
		curses.endwin()

	def draw(self):
		import time
		self.scr.erase()
		for i in range(1, len(self.pwd)):
			self.scr.addstr(i, 0, self.pwd[i])
		self.scr.refresh()

	def get_next_key(self):
		key = self.scr.getch()
		curses.flushinp()
		return key

