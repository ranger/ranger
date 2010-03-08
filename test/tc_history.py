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

if __name__ == '__main__': from __init__ import init; init()

from ranger.container import History
from unittest import TestCase, main
import unittest

class Test(TestCase):
	def test_history(self):
		hist = History(3)
		for i in range(6):
			hist.add(i)
		self.assertEqual([3,4,5], list(hist))

		hist.back()

		self.assertEqual(4, hist.current())
		self.assertEqual([3,4], list(hist))

		self.assertEqual(5, hist.top())

		hist.back()
		self.assertEqual(3, hist.current())
		self.assertEqual([3], list(hist))

		# no change if current == bottom
		self.assertEqual(hist.current(), hist.bottom())
		last = hist.current()
		hist.back()
		self.assertEqual(hist.current(), last)

		self.assertEqual(5, hist.top())

		hist.forward()
		hist.forward()
		self.assertEqual(5, hist.current())
		self.assertEqual([3,4,5], list(hist))


		self.assertEqual(3, hist.bottom())
		hist.add(6)
		self.assertEqual(4, hist.bottom())
		self.assertEqual([4,5,6], list(hist))

if __name__ == '__main__': main()
