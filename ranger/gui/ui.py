import curses

class UI():
	def __init__(self, env, commandlist, colorscheme):
		self.env = env
		self.commandlist = commandlist
		self.colorscheme = colorscheme

		self.widgets = []

		self.initialize()

		self.setup()
		self.resize()

	def initialize(self):
		self.win = curses.initscr()
		self.win.leaveok(1)
		self.win.keypad(1)

		curses.noecho()
		curses.halfdelay(20)
		curses.curs_set(0)
		curses.start_color()
		curses.use_default_colors()
		curses.mouseinterval(0)
		mask = curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION
		avail, old = curses.mousemask(mask)
		curses.mousemask(avail)

	def handle_mouse(self, fm):
		try:
			event = MouseEvent(curses.getmouse())
		except:
			return

		if event.pressed(1) or event.pressed(3):
			for widg in self.widgets:
				if widg.contains_point(event.y, event.x):
					widg.click(event, fm)
					break

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

#		from ranger.api import log
#		log(self.env.keybuffer)

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
		self.win.erase()
		for widg in self.widgets:
			widg.feed_env(self.env)
			widg.draw()
		self.win.refresh()

	def get_next_key(self):
		key = self.win.getch()
		curses.flushinp()
		return key


class MouseEvent():
	import curses
	PRESSED = [ 0,
			curses.BUTTON1_PRESSED,
			curses.BUTTON2_PRESSED,
			curses.BUTTON3_PRESSED,
			curses.BUTTON4_PRESSED ]

	def __init__(self, getmouse):
		_, self.x, self.y, _, self.bstate = getmouse
	
	def pressed(self, n):
		try:
			return (self.bstate & MouseEvent.PRESSED[n]) != 0
		except:
			return False
