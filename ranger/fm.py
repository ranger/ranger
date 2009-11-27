class FM():
	def __init__(self, environment):
		self.env = environment

	def feed(self, path, ui):
		self.ui = ui
		self.env.path = path
		self.env.enter_dir(path)

	def run(self):
		import time
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

	def move_left(self):
		self.env.enter_dir('..')

	def move_right(self):
		path = self.env.cf.path
		if not self.env.enter_dir(path):
			self.execute_file(path)

	def execute_file(self, path):
		import os
		self.ui.exit()
		os.system("mplayer '" + path + "'")
		self.ui.initialize()

	def move_pointer(self, relative = 0, absolute = None):
		self.env.cf = self.env.pwd.move_pointer(relative, absolute)

	def move_pointer_by_pages(self, relative = 0):
		self.env.cf = self.env.pwd.move_pointer(
				relative = int(relative * self.env.termsize[0]))

	def redraw(self):
		self.ui.redraw()

	def toggle_boolean_option(self, string):
		if isinstance(self.env.opt[string], bool):
			self.env.opt[string] ^= True
