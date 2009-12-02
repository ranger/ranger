from ranger.gui.widget import Widget as SuperClass
import curses

CONSOLE_MODES = tuple(':/?>!')

class WConsole(SuperClass):
	def __init__(self, win, colorscheme):
		from ranger.command import CommandList
		from ranger.conf.keys import initialize_console_commands
		SuperClass.__init__(self, win, colorscheme)
		self.mode = None
		self.visible = False
		self.commandlist = CommandList()
		initialize_console_commands(self.commandlist)
		self.last_cursor_mode = 1
		self.clear()

	def draw(self):
		if self.mode is None:
			return

		self.win.addstr(self.y, self.x, ":" + self.line)

	def finalize(self):
		try:
			self.win.move(self.y, self.x + self.pos + 1)
		except:
			pass

	def open(self, mode):
		if mode not in CONSOLE_MODES:
			return False

		self.last_cursor_mode = curses.curs_set(1)
		self.mode = mode
		self.focused = True
		self.visible = True
		return True

	def close(self):
		curses.curs_set(self.last_cursor_mode)
		self.focused = False
		self.visible = False
		if hasattr(self, 'on_close'):
			self.on_close()
	
	def clear(self):
		self.pos = 0
		self.line = ''
	
	def press(self, key, fm, env):
		from curses.ascii import ctrl, ESC
		from ranger.helper import log
		log(key)

		try:
			cmd = self.commandlist.paths[env.keybuffer]
		except KeyError:
			env.key_clear()
			return

		if cmd == self.commandlist.dummy_object:
			return

		cmd.execute(self, fm)
		env.key_clear()

	def type_key(self, key):
		if isinstance(key, int):
			key = chr(key)

		if self.pos == len(self.line):
			self.line += key
		else:
			self.line = self.line[:self.pos] + key + self.line[self.pos:]

		self.pos += len(key)

	def move(self, relative = 0, absolute = None):
		if absolute is not None:
			if absolute < 0:
				self.pos = len(self.line) + 1 + absolute
			else:
				self.pos = absolute

		self.pos = min(max(0, self.pos + relative), len(self.line))

	def delete_rest(self, direction):
		if direction > 0:
			self.line = self.line[:self.pos]
		else:
			self.line = self.line[self.pos:]
			self.pos = 0
	
	def delete(self, mod):
		pos = self.pos + mod

		self.line = self.line[0:pos] + self.line[pos+1:]
		self.move(relative = mod)

	def execute(self):
		self.line = ''
		self.pos = 0
		self.close()

