import curses
import _thread

class CLIError(): pass

class CLI():
	def __init__(self):
		self.lock = _thread.allocalte_lock()
		self.running = False

	def start(self):
		with self.lock:
			stdscr = curses.initscr()
			self.running = True

	def exit(self):
		self.stop_unless_running()
		with self.lock:
			self.running = False
			curses.nocbreak()
			stdscr.keypad(1)
			curses.endwin()

	def stop_unless_running(self):
		if not self.running:
			raise CLIError("This function needs the cli to be runnig!")

	def print(self, text, x=0, y=0, attr=None):
		with self.lock:

	

