# Copyright (C) 2010  David Barnett <davidbarnett2@gmail.com>
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

if __name__ == '__main__': from __init__ import init; init()

import unittest
from ranger.gui import ansi

class TestDisplayable(unittest.TestCase):
	def setUp(self):
		pass

	def tearDown(self):
		pass

	def test_char_len(self):
		ansi_string = "[0;30;40mX[0m"
		self.assertEqual(ansi.char_len(ansi_string), 1)

	def test_char_len2(self):
		ansi_string = "[0;30;40mXY[0m"
		self.assertEqual(ansi.char_len(ansi_string), 2)

	def test_char_len3(self):
		ansi_string = "[0;30;40mX[0;31;41mY"
		self.assertEqual(ansi.char_len(ansi_string), 2)

	def test_char_slice(self):
		ansi_string = "[0;30;40mX[0;31;41mY[0m"
		self.assertEqual(ansi.char_slice(ansi_string, 0, 1), "[0;30;40mX")

if __name__ == '__main__':
	unittest.main()
