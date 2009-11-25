import sys, os
import ui, debug, file, directory, fstype

class FM():
	def __init__(self, environment):
		self.env = environment

	def feed(self, path, ui):
		self.ui = ui
		self.env.path = path
		self.enter_dir(path)

	def enter_dir(self, path):
		# get the absolute path
		path = os.path.normpath(os.path.join(self.env.path, path))

		self.env.path = path
		self.env.pwd = self.env.get_directory(path)

		self.env.pwd.load_content()

		# build the pathway, a tuple of directory objects which lie
		# on the path to the current directory.
		pathway = []
		currentpath = '/'
		for dir in path.split('/'):
			currentpath = os.path.join(currentpath, dir)
			debug.log(currentpath)
			pathway.append(self.env.get_directory(currentpath))
		self.env.pathway = tuple(pathway)

		# set the current file.
		if len(self.env.pwd) > 0:
			self.env.cf = self.env.pwd[0]
		else:
			self.env.cf = None

	def run(self):
		while 1:
			try:
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

	def press(self, key):
		if (key == ord('q')):
			raise SystemExit()
		elif (key == ord('h')):
			self.enter_dir('..')
		elif (key == ord('l')):
			self.enter_dir(self.env.cf.path)

	def interrupt(self):
		import time
		self.buffer = ""
		time.sleep(0.2)

