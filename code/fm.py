import sys
import ui, debug, directory, fstype

class FM():
	def __init__(self, options, environment):
		self.options = options
		self.env = environment

	def setup(self, path, ui):
		self.ui = ui
		self.enter_dir(path)

	def enter_dir(self, path):
		self.env.path = path
		try:
			self.pwd = self.env.directories[path]
		except KeyError:
			self.env.pwd = directory.Directory(path)
			self.env.directories[path] = self.env.pwd

		self.env.pwd.load_content()
		if len(self.env.pwd) > 0: self.env.cf = self.env.pwd[0]

	def run(self):
		try:
			while 1:
				try:
#					if type(self.env.cf) is directory.Directory:
#						self.env.cf.load_content_once()
					self.ui.feed(self.env.directories, self.env.pwd, self.env.cf, self.env.termsize)
					self.ui.draw()
				except KeyboardInterrupt:
					self.interrupt()
				except:
					raise

				try:
					key = self.ui.get_next_key()
					self.press(key)
				except KeyboardInterrupt:
					self.interrupt()
		except:
			self.ui.exit()
			raise

	def press(self, key):
		if (key == ord('q')):
			raise SystemExit()

	def interrupt(self):
		import time
		self.buffer = ""
		time.sleep(0.2)

