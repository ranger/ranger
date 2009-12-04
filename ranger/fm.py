from os import devnull
from ranger.conf.apps import CustomApplications as Applications
null = open(devnull, 'a')

class FM():
	def __init__(self, environment, ui):
		self.env = environment
		self.ui = ui
		self.apps = Applications()

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

	def move_right(self, mode = 0):
		cf = self.env.cf
		if not self.env.enter_dir(cf):
			self.execute_file(cf, mode = mode)

	def history_go(self, relative):
		self.env.history_go(relative)
	
	def handle_mouse(self):
		self.ui.handle_mouse(self)

	def execute_file(self, files, app = '', flags = '', mode = 0):
		if type(files) not in (list, tuple):
			files = [files]

		self.apps.get(app)(
				mainfile = files[0],
				files = files,
				flags = flags,
				mode = mode,
				fm = self,
				stdin = None,
				apps = self.apps)
	
	def edit_file(self):
		if self.env.cf is None:
			return
		self.execute_file(self.env.cf, app = 'editor')

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

