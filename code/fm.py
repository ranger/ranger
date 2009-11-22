import time
import sys
from code import ui, debug

class FM():
	def __init__(self, options):
		self.singleton = None
		self.options = options
		self.ui = ui.UI()

	def run(self):
		try:
			while 1:
				try:
					self.ui.draw()
				except KeyboardInterrupt:
					self.interrupt()
				except:
					debug.log(sys.exc_info()[1])

				try:
					key = None
#					key = curses.getch()
#					curses.flushinp()
					self.press(key)
				except KeyboardInterrupt:
					self.interrupt()
		except:
			raise
			pass

	def press(self, key):
		pass

	def interrupt(self):
		self.buffer = ""
		time.sleep(0.2)

