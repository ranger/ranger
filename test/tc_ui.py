# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os.path
import sys
rangerpath = os.path.join(os.path.dirname(__file__), '..')
if sys.path[1] != rangerpath:
	sys.path[1:1] = [rangerpath]

import unittest
import curses

from ranger.gui import ui

from testlib import Fake, OK, raise_ok

ui.curses = Fake()

class Test(unittest.TestCase):
	def setUp(self):

		self.fm = Fake()
		self.ui = ui.UI(env=Fake(), fm=self.fm)

		def fakesetup():
			self.ui.widget = Fake()
			self.ui.add_child(self.ui.widget)
		self.ui.setup = fakesetup

		self.ui.initialize()

	def tearDown(self):
		self.ui.destroy()

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
