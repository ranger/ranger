# coding=utf-8
if __name__ == '__main__': from __init__ import init; init()
from unittest import TestCase, main

from ranger.ext.tree import Tree
from ranger.container.keymap import *

import sys

class PressTestCase(TestCase):
	"""Some useful methods for the actual test"""
	def _mkpress(self, keybuffer, keymap):
		def press(keys):
			keybuffer.clear()
			match = keybuffer.simulate_press(keys)
			self.assertFalse(keybuffer.failure,
					"parsing keys '"+keys+"' did fail!")
			self.assertTrue(keybuffer.done,
					"parsing keys '"+keys+"' did not complete!")
			arg = CommandArgs(None, None, keybuffer)
			self.assert_(match.function, "No function found! " + \
					str(match.__dict__))
			return match.function(arg)
		return press

	def assertPressFails(self, kb, keys):
		kb.clear()
		kb.simulate_press(keys)
		self.assertTrue(kb.failure, "Keypress did not fail as expected")
		kb.clear()

	def assertPressIncomplete(self, kb, keys):
		kb.clear()
		kb.simulate_press(keys)
		self.assertFalse(kb.failure, "Keypress failed, expected incomplete")
		self.assertFalse(kb.done, "Keypress done which was unexpected")
		kb.clear()

class Test(PressTestCase):
	"""The test cases"""
	def test_translate_keys(self):
		def test(string, *args):
			if not args:
				args = (string, )
			self.assertEqual(ordtuple(*args), tuple(translate_keys(string)))

		def ordtuple(*args):
			lst = []
			for arg in args:
				if isinstance(arg, str):
					lst.extend(ord(c) for c in arg)
				else:
					lst.append(arg)
			return tuple(lst)

		test('k')
		test('kj')
		test('k<dir>', 'k', DIRKEY)
		test('k<ANY>z<any>', 'k', ANYKEY, 'z', ANYKEY)
		test('k<anY>z<dir>', 'k', ANYKEY, 'z', DIRKEY)
		test('<cr>', "\n")
		test('<tab><tab><cr>', "\t\t\n")
		test('<')
		test('>')
		test('<C-a>', 1)
		test('<C-b>', 2)
		for i in range(1, 26):
			test('<C-' + chr(i+ord('a')-1) + '>', i)
		test('k<a')
		test('k<anz>')
		test('k<a<nz>')
		test('k<a<nz>')
		test('k<a<>nz>')
		test('>nz>')

	def test_alias(self):
		def add_dirs(arg):
			n = 0
			for dir in arg.directions:
				n += dir.down
			return n
		def return5(_):
			return 5

		directions = KeyMap()
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))
		directions.add('<CR>', alias='j')

		base = KeyMap()
		base.add(add_dirs, 'a<dir>')
		base.add(add_dirs, 'b<dir>')
		base.add(add_dirs, 'x<dir>x<dir>')
		base.add(return5, 'f')
		base.add('yy', alias='y')
		base.add('!', alias='!')

		other = KeyMap()
		other.add('b<dir>b<dir>', alias='x<dir>x<dir>')
		other.add(add_dirs, 'c<dir>')
		other.add('g', alias='f')

		km = base.merge(other)
		kb = KeyBuffer(km, directions)

		press = self._mkpress(kb, km)

		self.assertEqual(1, press('aj'))
		self.assertEqual(2, press('bjbj'))
		self.assertEqual(1, press('cj'))
		self.assertEqual(1, press('c<CR>'))

		self.assertEqual(5, press('f'))
		self.assertEqual(5, press('g'))

		for n in range(1, 50):
			self.assertPressIncomplete(kb, 'y' * n)

		for n in range(1, 5):
			self.assertPressFails(kb, '!' * n)

	def test_tree(self):
		t = Tree()
		t.set('abcd', "Yes")
		self.assertEqual("Yes", t.traverse('abcd'))
		self.assertRaises(KeyError, t.traverse, 'abcde')
		self.assertRaises(KeyError, t.traverse, 'xyz')
		self.assert_(isinstance(t.traverse('abc'), Tree))

		t2 = Tree()
		self.assertRaises(KeyError, t2.set, 'axy', "Lol", force=False)
		t2.set('axx', 'ololol')
		t2.set('axyy', "Lol")
		self.assertEqual("Yes", t.traverse('abcd'))
		self.assertRaises(KeyError, t2.traverse, 'abcd')
		self.assertEqual("Lol", t2.traverse('axyy'))
		self.assertEqual("ololol", t2.traverse('axx'))

		t2.unset('axyy')
		self.assertEqual("ololol", t2.traverse('axx'))
		self.assertRaises(KeyError, t2.traverse, 'axyy')
		self.assertRaises(KeyError, t2.traverse, 'axy')

		t2.unset('a')
		self.assertRaises(KeyError, t2.traverse, 'abcd')
		self.assertRaises(KeyError, t2.traverse, 'a')
		self.assert_(t2.empty())

	def test_merge_trees(self):
		def makeTreeA():
			t = Tree()
			t.set('aaaX', 1)
			t.set('aaaY', 2)
			t.set('aaaZ', 3)
			t.set('bbbA', 11)
			t.set('bbbB', 12)
			t.set('bbbC', 13)
			t.set('bbbD', 14)
			t.set('bP', 21)
			t.set('bQ', 22)
			return t

		def makeTreeB():
			u = Tree()
			u.set('aaaX', 0)
			u.set('bbbC', 'Yes')
			u.set('bbbD', None)
			u.set('bbbE', 15)
			u.set('bbbF', 16)
			u.set('bQ', 22)
			u.set('bR', 23)
			u.set('ffff', 1337)
			return u

		# test 1
		t = Tree('a')
		u = Tree('b')
		merged = t.merge(u)
		self.assertEqual('b', merged._tree)

		# test 2
		t = Tree('a')
		u = makeTreeA()
		merged = t.merge(u)
		self.assertEqual(u._tree, merged._tree)

		# test 3
		t = makeTreeA()
		u = makeTreeB()
		v = t.merge(u)

		self.assertEqual(0, v['aaaX'])
		self.assertEqual(2, v['aaaY'])
		self.assertEqual(3, v['aaaZ'])
		self.assertEqual(11, v['bbbA'])
		self.assertEqual('Yes', v['bbbC'])
		self.assertEqual(None, v['bbbD'])
		self.assertEqual(15, v['bbbE'])
		self.assertEqual(16, v['bbbF'])
		self.assertRaises(KeyError, t.__getitem__, 'bbbG')
		self.assertEqual(21, v['bP'])
		self.assertEqual(22, v['bQ'])
		self.assertEqual(23, v['bR'])
		self.assertEqual(1337, v['ffff'])

		# merge shouldn't be destructive
		self.assertEqual(makeTreeA()._tree, t._tree)
		self.assertEqual(makeTreeB()._tree, u._tree)

		v['fff'].replace('Lolz')
		self.assertEqual('Lolz', v['fff'])

		v['aaa'].replace('Very bad')
		v.plow('qqqqqqq').replace('eww.')

		self.assertEqual(makeTreeA()._tree, t._tree)
		self.assertEqual(makeTreeB()._tree, u._tree)

	def test_add(self):
		c = KeyMap()
		c.add(lambda *_: 'lolz', 'aa', 'b')
		self.assert_(c['aa'].function(), 'lolz')
		@c.add('a', 'c')
		def test():
			return 5
		self.assert_(c['b'].function(), 'lolz')
		self.assert_(c['c'].function(), 5)
		self.assert_(c['a'].function(), 5)

	def test_quantifier(self):
		km = KeyMap()
		directions = KeyMap()
		kb = KeyBuffer(km, directions)
		def n(value):
			"""return n or value"""
			def fnc(arg=None):
				if arg is None or arg.n is None:
					return value
				return arg.n
			return fnc
		km.add(n(5), 'p')
		press = self._mkpress(kb, km)
		self.assertEqual(5, press('p'))
		self.assertEqual(3, press('3p'))
		self.assertEqual(6223, press('6223p'))

	def test_direction(self):
		km = KeyMap()
		directions = KeyMap()
		kb = KeyBuffer(km, directions)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))
		def nd(arg):
			""" n * direction """
			n = arg.n is None and 1 or arg.n
			dir = arg.direction is None and Direction(down=1) \
					or arg.direction
			return n * dir.down
		km.add(nd, 'd<dir>')
		km.add('dd', func=nd, with_direction=False)

		press = self._mkpress(kb, km)

		self.assertPressIncomplete(kb, 'd')
		self.assertEqual(  1, press('dj'))
		self.assertEqual(  3, press('3ddj'))
		self.assertEqual( 15, press('3d5j'))
		self.assertEqual(-15, press('3d5k'))
		# supporting this kind of key combination would be too confusing:
		# self.assertEqual( 15, press('3d5d'))
		self.assertEqual(  3, press('3dd'))
		self.assertEqual(  33, press('33dd'))
		self.assertEqual(  1, press('dd'))

		km.add(nd, 'x<dir>')
		km.add('xxxx', func=nd, with_direction=False)

		self.assertEqual(1, press('xxxxj'))
		self.assertEqual(1, press('xxxxjsomeinvalitchars'))

		# these combinations should break:
		self.assertPressFails(kb, 'xxxj')
		self.assertPressFails(kb, 'xxj')
		self.assertPressFails(kb, 'xxkldfjalksdjklsfsldkj')
		self.assertPressFails(kb, 'xyj')
		self.assertPressIncomplete(kb, 'x') # direction missing

	def test_any_key(self):
		km = KeyMap()
		directions = KeyMap()
		kb = KeyBuffer(km, directions)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))

		directions.add('g<any>', dir=Direction(down=-1))

		def cat(arg):
			n = arg.n is None and 1 or arg.n
			return ''.join(chr(c) for c in arg.matches) * n

		km.add(cat, 'return<any>')
		km.add(cat, 'cat4<any><any><any><any>')
		km.add(cat, 'foo<dir><any>')

		press = self._mkpress(kb, km)

		self.assertEqual('x', press('returnx'))
		self.assertEqual('abcd', press('cat4abcd'))
		self.assertEqual('abcdabcd', press('2cat4abcd'))
		self.assertEqual('55555', press('5return5'))

		self.assertEqual('x', press('foojx'))
		self.assertPressFails(kb, 'fooggx')  # ANYKEY forbidden in DIRECTION

		km.add(lambda _: Ellipsis, '<any>')
		self.assertEqual('x', press('returnx'))
		self.assertEqual('abcd', press('cat4abcd'))
		self.assertEqual(Ellipsis, press('2cat4abcd'))
		self.assertEqual(Ellipsis, press('5return5'))
		self.assertEqual(Ellipsis, press('g'))
		self.assertEqual(Ellipsis, press('ß'))
		self.assertEqual(Ellipsis, press('ア'))
		self.assertEqual(Ellipsis, press('9'))

	def test_multiple_directions(self):
		km = KeyMap()
		directions = KeyMap()
		kb = KeyBuffer(km, directions)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))

		def add_dirs(arg):
			n = 0
			for dir in arg.directions:
				n += dir.down
			return n

		km.add(add_dirs, 'x<dir>y<dir>')
		km.add(add_dirs, 'four<dir><dir><dir><dir>')

		press = self._mkpress(kb, km)

		self.assertEqual(2, press('xjyj'))
		self.assertEqual(0, press('fourjkkj'))
		self.assertEqual(2, press('four2j4k2j2j'))
		self.assertEqual(10, press('four1j2j3j4j'))
		self.assertEqual(10, press('four1j2j3j4jafslkdfjkldj'))

	def test_corruptions(self):
		km = KeyMap()
		directions = KeyMap()
		kb = KeyBuffer(km, directions)
		press = self._mkpress(kb, km)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))
		km.add('xxx', func=lambda _: 1)

		self.assertEqual(1, press('xxx'))

		# corrupt the tree
		tup = tuple(translate_keys('xxx'))
		x = ord('x')
		km._tree[x][x][x] = "Boo"

		self.assertPressFails(kb, 'xxy')
		self.assertPressFails(kb, 'xzy')
		self.assertPressIncomplete(kb, 'xx')
		self.assertPressIncomplete(kb, 'x')
		if not sys.flags.optimize:
			self.assertRaises(AssertionError, kb.simulate_press, 'xxx')
		kb.clear()

	def test_directions_as_functions(self):
		km = KeyMap()
		directions = KeyMap()
		kb = KeyBuffer(km, directions)
		press = self._mkpress(kb, km)

		def move(arg):
			return arg.direction.down

		directions.add('j', dir=Direction(down=1))
		directions.add('s', alias='j')
		directions.add('k', dir=Direction(down=-1))
		km.add('<dir>', func=move)

		self.assertEqual(1, press('j'))
		self.assertEqual(1, press('j'))
		self.assertEqual(1, press('j'))
		self.assertEqual(1, press('j'))
		self.assertEqual(1, press('j'))
		self.assertEqual(1, press('s'))
		self.assertEqual(1, press('s'))
		self.assertEqual(1, press('s'))
		self.assertEqual(1, press('s'))
		self.assertEqual(1, press('s'))
		self.assertEqual(-1, press('k'))
		self.assertEqual(-1, press('k'))
		self.assertEqual(-1, press('k'))

		km.add('k', func=lambda _: 'love')

		self.assertEqual(1, press('j'))
		self.assertEqual('love', press('k'))

		self.assertEqual(40, press('40j'))

		km.add('<dir><dir><any><any>', func=move)

		self.assertEqual(40, press('40jkhl'))

	def test_tree_deep_copy(self):
		t = Tree()
		s = t.plow('abcd')
		s.replace('X')
		u = t.copy()
		self.assertEqual(t._tree, u._tree)
		s = t.traverse('abc')
		s.replace('Y')
		self.assertNotEqual(t._tree, u._tree)


if __name__ == '__main__': main()
