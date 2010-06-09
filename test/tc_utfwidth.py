# -*- encoding: utf8 -*-
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

from unittest import TestCase, main
from ranger.ext.utfwidth import *

a_ascii = "a"      # width = 1, bytes = 1
a_umlaut = "ä"     # width = 1, bytes = 2
a_katakana = "ア"  # width = 2, bytes = 3
# need one with width = 1 & bytes = 3

class Test(TestCase):
	def test_utf_byte_length(self):
		self.assertEqual(1, utf_byte_length(a_ascii))
		self.assertEqual(2, utf_byte_length(a_umlaut))
		self.assertEqual(3, utf_byte_length(a_katakana))

	def test_uwid(self):
		self.assertEqual(1, uwid(a_ascii))
		self.assertEqual(1, uwid(a_umlaut))
		self.assertEqual(2, uwid(a_katakana))
		self.assertEqual(3, uwid(a_katakana + a_umlaut))
		self.assertEqual(4, uwid("asdf"))
		self.assertEqual(5, uwid("löööl"))
		self.assertEqual(6, uwid("バババ"))

if __name__ == '__main__': main()
