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
from ranger.ext.direction import Direction
from ranger.ext.openstruct import OpenStruct

class TestDirections(unittest.TestCase):
	def test_symmetry(self):
		d1 = Direction(right=4, down=7, relative=True)
		d2 = Direction(left=-4, up=-7, absolute=False)

		def subtest(d):
			self.assertEqual(4, d.right())
			self.assertEqual(7, d.down())
			self.assertEqual(-4, d.left())
			self.assertEqual(-7, d.up())
			self.assertEqual(True, d.relative())
			self.assertEqual(False, d.absolute())

			self.assertTrue(d.horizontal())
			self.assertTrue(d.vertical())

		subtest(d1)
		subtest(d2)

	def test_conflicts(self):
		d3 = Direction(right=5, left=2, up=3, down=6,
				absolute=True, relative=True)
		self.assertEqual(d3.right(), -d3.left())
		self.assertEqual(d3.left(), -d3.right())
		self.assertEqual(d3.up(), -d3.down())
		self.assertEqual(d3.down(), -d3.up())
		self.assertEqual(d3.absolute(), not d3.relative())
		self.assertEqual(d3.relative(), not d3.absolute())

	def test_copy(self):
		d = Direction(right=5)
		c = d.copy()
		self.assertEqual(c.right(), d.right())
		d['right'] += 3
		self.assertNotEqual(c.right(), d.right())
		c['right'] += 3
		self.assertEqual(c.right(), d.right())

		self.assertFalse(d.vertical())
		self.assertTrue(d.horizontal())

#	Doesn't work in python2?
#	def test_duck_typing(self):
#		dct = dict(right=7, down=-3)
#		self.assertEqual(-7, Direction.left(dct))
#		self.assertEqual(3, Direction.up(dct))

	def test_move(self):
		d = Direction(pages=True)
		self.assertEqual(3, d.move(direction=3))
		self.assertEqual(5, d.move(direction=3, current=2))
		self.assertEqual(15, d.move(direction=3, pagesize=5))
		self.assertEqual(9, d.move(direction=3, pagesize=5, maximum=10))
		self.assertEqual(18, d.move(direction=9, override=2))
		d2 = Direction(absolute=True)
		self.assertEqual(5, d2.move(direction=9, override=5))

	def test_select(self):
		d = Direction(down=3)
		lst = list(range(100))
		self.assertEqual((6, [3,4,5,6]), d.select(current=3, pagesize=10, override=None, lst=lst))
		d = Direction(down=3, pages=True)
		self.assertEqual((9, [3,4,5,6,7,8,9]), d.select(current=3, pagesize=2, override=None, lst=lst))

if __name__ == '__main__':
	unittest.main()

