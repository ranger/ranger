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

	def test_mount_path(self):
		# assuming ismount() is used

		def my_ismount(path):
			depth = path.count('/')
			if path.startswith('/media'):
				return depth == 0 or depth == 2
			return depth <= 1

		from ranger.ext import mount_path
		mount_path.ismount = my_ismount

		mp = mount_path.mount_path

		self.assertEqual('/home', mp('/home/hut/porn/bondage'))
		self.assertEqual('/', mp('/'))
		self.assertEqual('/media/sdb1', mp('/media/sdb1/foo/bar'))
		self.assertEqual('/media/sdc2', mp('/media/sdc2/a/b/c/d/e'))

		# TODO: links are not tested but I don't see how its possible
		# without messing around with mounts.
		# self.assertEqual('/media/foo',
		#     mount_path('/media/bar/some_link_to_a_foo_subdirectory'))

	def test_openstruct(self):
		from ranger.ext.openstruct import OpenStruct
		from random import randint, choice
		from string import ascii_letters

		os = OpenStruct(a='a')
		self.assertEqual(os.a, 'a')
		self.assertRaises(AttributeError, getattr, os, 'b')

		dictionary = {'foo': 'bar', 'zoo': 'zar'}
		os = OpenStruct(dictionary)
		self.assertEqual(os.foo, 'bar')
		self.assertEqual(os.zoo, 'zar')
		self.assertRaises(AttributeError, getattr, os, 'sdklfj')

		for i in range(100):
			attr_name = ''.join(choice(ascii_letters) \
				for x in range(randint(3,9)))
			value = randint(100,999)
			if not attr_name in os:
				self.assertRaises(AttributeError, getattr, os, attr_name)
			setattr(os, attr_name, value)
			value2 = randint(100,999)
			setattr(os, attr_name, value2)
			self.assertEqual(value2, getattr(os, attr_name))


if __name__ == '__main__':
	unittest.main()
