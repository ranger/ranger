if __name__ == '__main__': from __init__ import init; init()

from unittest import TestCase, main
from ranger.container.commandlist import CommandList as CL

class Test(TestCase):
	def assertKeyError(self, obj, key):
		self.assertRaises(KeyError, obj.__getitem__, key)

	def test_commandist(self):
		cl = CL()
		fnc = lambda arg: 1
		dmy = cl.dummy_object

		cl.bind(fnc, 'aaaa')
		cl.rebuild_paths()

		self.assertEqual(dmy, cl['a'])
		self.assertEqual(dmy, cl['aa'])
		self.assertEqual(dmy, cl['aaa'])
		self.assertEqual(fnc, cl['aaaa'].execute)
		self.assertKeyError(cl, 'aabb')
		self.assertKeyError(cl, 'aaaaa')

		cl.bind(fnc, 'aabb')
		cl.rebuild_paths()

		self.assertEqual(dmy, cl['a'])
		self.assertEqual(dmy, cl['aa'])
		self.assertEqual(dmy, cl['aab'])
		self.assertEqual(fnc, cl['aabb'].execute)
		self.assertEqual(dmy, cl['aaa'])
		self.assertEqual(fnc, cl['aaaa'].execute)

		cl.unbind('aabb')
		cl.rebuild_paths()

		self.assertEqual(dmy, cl['a'])
		self.assertEqual(dmy, cl['aa'])
		self.assertKeyError(cl, 'aabb')
		self.assertKeyError(cl, 'aab')
		self.assertEqual(dmy, cl['aaa'])
		self.assertEqual(fnc, cl['aaaa'].execute)

		hint_text = 'some tip blablablba'
		cl.hint(hint_text, 'aa')
		cl.rebuild_paths()

		self.assertEqual(dmy, cl['a'])
		self.assertEqual(hint_text, cl['aa'].text)
		self.assertEqual(dmy, cl['aaa'])
		self.assertEqual(fnc, cl['aaaa'].execute)

		cl.alias('aaaa', 'c')
		cl.rebuild_paths()
		self.assertEqual(cl['c'], cl['aaaa'])
		cl.unbind('c')
		cl.rebuild_paths()
		self.assertEqual(fnc, cl['aaaa'].execute)
		self.assertKeyError(cl, 'c')

		cl.clear()
		self.assertKeyError(cl, 'a')
		self.assertKeyError(cl, 'aa')
		self.assertKeyError(cl, 'aaa')
		self.assertKeyError(cl, 'aaaa')
		self.assertKeyError(cl, 'aab')
		self.assertKeyError(cl, 'aabb')


if __name__ == '__main__': main()
