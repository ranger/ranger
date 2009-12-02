from os import devnull
null = open(devnull, 'a')

class FM():
	def __init__(self, environment, ui):
		self.env = environment
		self.ui = ui

	def run(self):
		self.env.enter_dir(self.env.path)

		while 1:
			try:
				self.ui.draw()
				key = self.ui.get_next_key()
				self.ui.press(key, self)
			except KeyboardInterrupt:
				self.ui.press(3, self)
			except:
				raise
	
	def interrupt(self):
		import time
		self.env.key_clear()
		try:
			time.sleep(0.2)
		except KeyboardInterrupt:
			raise SystemExit()

	def resize(self):
		self.ui.resize()

	def exit(self):
		raise SystemExit()

	def enter_dir(self, path):
		self.env.enter_dir(path)

	def move_left(self):
		self.env.enter_dir('..')

	def move_right(self):
		try:
			path = self.env.cf.path
			if not self.env.enter_dir(path):
				self.execute_file(path)
		except AttributeError:
			pass

	def history_go(self, relative):
		self.env.history_go(relative)
	
	def handle_mouse(self):
		self.ui.handle_mouse(self)

	def execute_file(self, path):
		from subprocess import Popen
		Popen(('mplayer', '-fs', path), stdout = null, stderr = null)

	def edit_file(self):
		from subprocess import Popen
		import os
		if self.env.cf is None: return

		self.ui.exit()

		p = Popen(('vim', self.env.cf.path))
		os.waitpid(p.pid, 0)

		self.ui.initialize()

	def open_console(self, mode = ':'):
		if self.ui.can('open_console'):
			self.ui.open_console(mode)

	def move_pointer(self, relative = 0, absolute = None):
		self.env.cf = self.env.pwd.move_pointer(relative, absolute)

	def move_pointer_by_pages(self, relative):
		self.env.cf = self.env.pwd.move_pointer(
				relative = int(relative * self.env.termsize[0]))

	def scroll(self, relative):
		if self.ui.can('scroll'):
			self.ui.scroll(relative)
			self.env.cf = self.env.pwd.pointed_file

	def redraw(self):
		self.ui.redraw()

	def reset(self):
		old_path = self.env.pwd.path
		self.env.directories = {}
		self.enter_dir(old_path)

	def toggle_boolean_option(self, string):
		if isinstance(self.env.opt[string], bool):
			self.env.opt[string] ^= True

