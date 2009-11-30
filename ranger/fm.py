from os import devnull
null = open(devnull, 'a')

class FM():
	def __init__(self, environment, ui):
		self.env = environment
		self.ui = ui

	def run(self):
		import time

		self.env.enter_dir(self.env.path)

		while 1:
			try:
				self.ui.draw()
				key = self.ui.get_next_key()
				self.ui.press(key, self)
			except KeyboardInterrupt:
				self.env.key_clear()
				time.sleep(0.2)
			except:
				raise

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

	def move_pointer(self, relative = 0, absolute = None):
		self.env.cf = self.env.pwd.move_pointer(relative, absolute)

	def move_pointer_by_pages(self, relative = 0):
		self.env.cf = self.env.pwd.move_pointer(
				relative = int(relative * self.env.termsize[0]))

	def redraw(self):
		self.ui.redraw()

	def reset(self):
		old_path = self.env.pwd.path
		self.env.directories = {}
		self.enter_dir(old_path)

	def toggle_boolean_option(self, string):
		if isinstance(self.env.opt[string], bool):
			self.env.opt[string] ^= True

