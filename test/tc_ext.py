if __name__ == '__main__': from __init__ import init; init()
import unittest
from collections import deque

from ranger.ext.iter_tools import *

class TestCases(unittest.TestCase):
	def test_flatten(self):
		def f(x):
			return list(flatten(x))

		self.assertEqual(
			[1,2,3,4,5],
			f([1,2,3,4,5]))
		self.assertEqual(
			[1,2,3,4,5],
			f([1,[2,3],4,5]))
		self.assertEqual(
			[1,2,3,4,5],
			f([[1,[2,3]],4,5]))
		self.assertEqual(
			[],
			f([[[[]]]]))
		self.assertEqual(
			['a', 'b', 'fskldfjl'],
			f(['a', ('b', 'fskldfjl')]))
		self.assertEqual(
			['a', 'b', 'fskldfjl'],
			f(['a', deque(['b', 'fskldfjl'])]))
		self.assertEqual(
			set([3.5, 4.3, 5.2, 6.0]),
			set(f([6.0, set((3.5, 4.3)), (5.2, )])))

	def test_unique(self):
		def u(x):
			return list(unique(x))

		self.assertEqual(
			[1,2,3],
			u([1,2,3]))
		self.assertEqual(
			[1,2,3],
			u([1,2,3,2,1]))
		self.assertEqual(
			[1,2,3],
			u([1,2,3,1,2,3,2,2,3,1,2,3,1,2,3,2,3,2,1]))
		self.assertEqual(
			[1,[2,3]],
			u([1,[2,3],1,[2,3],[2,3],1,[2,3],1,[2,3],[2,3],1]))

	def test_unique_keeps_type(self):
		def u(x):
			return unique(x)

		self.assertEqual(
			[1,2,3],
			u([1,2,3,1]))
		self.assertEqual(
			(1,2,3),
			u((1,2,3,1)))
		self.assertEqual(
			set((1,2,3)),
			u(set((1,2,3,1))))
		self.assertEqual(
			deque((1,2,3)),
			u(deque((1,2,3,1))))

if __name__ == '__main__':
	unittest.main()
