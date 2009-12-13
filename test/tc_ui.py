if __name__ == '__main__': from __init__ import init; init()

import unittest
import curses

from ranger.gui import ui

from test import Fake, OK, raise_ok

ui.curses = Fake()

class Test(unittest.TestCase):
	def setUp(self):

		self.fm = Fake()
		self.ui = ui.UI(env=Fake(), fm=self.fm)

		def fakesetup():
			self.ui.widget = Fake()
			self.ui.add_obj(self.ui.widget)
		self.ui.setup = fakesetup

		self.ui.initialize()

	def tearDown(self):
		self.ui.destroy()
	
	def test_scrolling(self):
		# test whether scrolling works
		self.fm.scroll = raise_ok
		self.ui.get_focused_obj = lambda: False

		ui.curses.getmouse = lambda: (0, 0, 0, 0, curses.BUTTON2_PRESSED)
		self.assertRaises(OK, self.ui.handle_mouse)

		ui.curses.getmouse = lambda: (0, 0, 0, 0, curses.BUTTON4_PRESSED)
		self.assertRaises(OK, self.ui.handle_mouse)
	
	def test_passing(self):
		# Test whether certain method calls are passed to widgets
		widget = self.ui.widget

		widget.draw = raise_ok
		self.assertRaises(OK, self.ui.draw)
		widget.__clear__()

		widget.finalize = raise_ok
		self.assertRaises(OK, self.ui.finalize)
		widget.__clear__()

		widget.press = raise_ok
		random_key = 123
		self.assertRaises(OK, self.ui.handle_key, random_key)
		widget.__clear__()

		widget.destroy = raise_ok
		self.assertRaises(OK, self.ui.destroy)
		widget.__clear__()

if __name__ == '__main__':
	unittest.main()
