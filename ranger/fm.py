import sys
#LOGFILE = '/tmp/errorlog'
#f = open(LOGFILE, 'a')
#f.write(str(tuple(sys.path)) + "\n")
#f.close()
#import code.ui, code.debug, code.file, code.directory, code.fstype


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

	def exit(self):
		raise SystemExit()

	def move_left(self):
		self.env.enter_dir('..')

	def move_right(self):
		self.env.enter_dir(self.env.cf.path)

	def move_relative(self):
		pass

