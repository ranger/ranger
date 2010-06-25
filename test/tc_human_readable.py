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

import unittest
from ranger.ext.human_readable import human_readable as hr

class HumanReadableTest(unittest.TestCase):
	def test_basic(self):
		self.assertEqual("0", hr(0))
		self.assertEqual("1 B", hr(1))
		self.assertEqual("1 K", hr(2 ** 10))
		self.assertEqual("1 M", hr(2 ** 20))
		self.assertEqual("1 G", hr(2 ** 30))
		self.assertEqual(">9000", hr(2 ** 100))

	def test_big(self):
		self.assertEqual("1023 G", hr(2 ** 30 * 1023))
		self.assertEqual("1024 G", hr(2 ** 40 - 1))
		self.assertEqual("1 T",    hr(2 ** 40))

	def test_small(self):
		self.assertEqual("1000 B", hr(1000))
		self.assertEqual("1.66 M", hr(1.66 * 2 ** 20))
		self.assertEqual("1.46 K", hr(1500))
		self.assertEqual("1.5 K",  hr(2 ** 10 + 2 ** 9))
		self.assertEqual("1.5 K",  hr(2 ** 10 + 2 ** 9 - 1))

	def test_no_exponent(self):
		for i in range(2 ** 10, 2 ** 20, 512):
			self.assertTrue('e' not in hr(i), "%d => %s" % (i, hr(i)))

if __name__ == '__main__':
	unittest.main()
