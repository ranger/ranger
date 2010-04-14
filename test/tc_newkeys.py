# coding=utf-8
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
from unittest import TestCase, main

from ranger.ext.tree import Tree
from ranger.container.keymap import *

import sys

class PressTestCase(TestCase):
	"""Some useful methods for the actual test"""
	def _mkpress(self, keybuffer, _=0):
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
	def test_passive_action(self):
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

		km.map('ppp', n(5))
		km.map('pp<bg>', n(8))
		km.map('pp<dir>', n(2))
		directions.map('j', dir=Direction(down=1))

		press = self._mkpress(kb, km)
		self.assertEqual(5, press('ppp'))
		self.assertEqual(3, press('3ppp'))

		self.assertEqual(2, press('ppj'))

		kb.clear()
		match = kb.simulate_press('pp')
		args = CommandArgs(0, 0, kb)
		self.assert_(match)
		self.assert_(match.function)
		self.assertEqual(8, match.function(args))

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

		# 1 argument means: assume nothing is translated.
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
		test('<A-x>', 27, ord('x'))
		test('<a-o>', 27, ord('o'))
		test('k<a')
		test('k<anz>')
		test('k<a<nz>')
		test('k<a<nz>')
		test('k<a<>nz>')
		test('>nz>')

	def test_alias(self):
		def add_dirs(arg):
			return sum(dir.down() for dir in arg.directions)
		def return5(_):
			return 5

		directions = KeyMap()
		directions.map('j', dir=Direction(down=1))
		directions.map('k', dir=Direction(down=-1))
		directions.map('<CR>', alias='j')
		directions.map('@', alias='<CR>')

		base = KeyMap()
		base.map('a<dir>', add_dirs)
		base.map('b<dir>', add_dirs)
		base.map('x<dir>x<dir>', add_dirs)
		base.map('f', return5)
		base.map('yy', alias='y')
		base.map('!', alias='!')

		other = KeyMap()
		other.map('b<dir>b<dir>', alias='x<dir>x<dir>')
		other.map('c<dir>', add_dirs)
		other.map('g', alias='f')

		km = base.merge(other, copy=True)
		kb = KeyBuffer(km, directions)

		press = self._mkpress(kb, km)

		self.assertEqual(1, press('aj'))
		self.assertEqual(2, press('bjbj'))
		self.assertEqual(1, press('cj'))
		self.assertEqual(1, press('c<CR>'))

		self.assertEqual(5, press('f'))
		self.assertEqual(5, press('g'))
		self.assertEqual(press('c<CR>'), press('c@'))
		self.assertEqual(press('c<CR>'), press('c@'))
		self.assertEqual(press('c<CR>'), press('c@'))

		for n in range(1, 10):
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
		merged = t.merge(u, copy=True)
		self.assertEqual('b', merged._tree)

		# test 2
		t = Tree('a')
		u = makeTreeA()
		merged = t.merge(u, copy=True)
		self.assertEqual(u._tree, merged._tree)

		# test 3
		t = makeTreeA()
		u = makeTreeB()
		v = t.merge(u, copy=True)

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
		c.map('aa', 'b', lambda *_: 'lolz')
		self.assert_(c['aa'].function(), 'lolz')
		@c.map('a', 'c')
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
		km.map('p', n(5))
		press = self._mkpress(kb, km)
		self.assertEqual(5, press('p'))
		self.assertEqual(3, press('3p'))
		self.assertEqual(6223, press('6223p'))

	def test_direction(self):
		km = KeyMap()
		directions = KeyMap()
		kb = KeyBuffer(km, directions)
		directions.map('j', dir=Direction(down=1))
		directions.map('k', dir=Direction(down=-1))
		def nd(arg):
			""" n * direction """
			n = arg.n is None and 1 or arg.n
			dir = arg.direction is None and Direction(down=1) \
					or arg.direction
			return n * dir.down()
		km.map('d<dir>', nd)
		km.map('dd', func=nd)

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

		km.map('x<dir>', nd)
		km.map('xxxx', func=nd)

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
		directions.map('j', dir=Direction(down=1))
		directions.map('k', dir=Direction(down=-1))

		directions.map('g<any>', dir=Direction(down=-1))

		def cat(arg):
			n = arg.n is None and 1 or arg.n
			return ''.join(chr(c) for c in arg.matches) * n

		km.map('return<any>', cat)
		km.map('cat4<any><any><any><any>', cat)
		km.map('foo<dir><any>', cat)

		press = self._mkpress(kb, km)

		self.assertEqual('x', press('returnx'))
		self.assertEqual('abcd', press('cat4abcd'))
		self.assertEqual('abcdabcd', press('2cat4abcd'))
		self.assertEqual('55555', press('5return5'))

		self.assertEqual('x', press('foojx'))
		self.assertPressFails(kb, 'fooggx')  # ANYKEY forbidden in DIRECTION

		km.map('<any>', lambda _: Ellipsis)
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
		directions.map('j', dir=Direction(down=1))
		directions.map('k', dir=Direction(down=-1))

		def add_dirs(arg):
			return sum(dir.down() for dir in arg.directions)

		km.map('x<dir>y<dir>', add_dirs)
		km.map('four<dir><dir><dir><dir>', add_dirs)

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
		directions.map('j', dir=Direction(down=1))
		directions.map('k', dir=Direction(down=-1))
		km.map('xxx', lambda _: 1)

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
			return arg.direction.down()

		directions.map('j', dir=Direction(down=1))
		directions.map('s', alias='j')
		directions.map('k', dir=Direction(down=-1))
		km.map('<dir>', func=move)

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

		km.map('k', func=lambda _: 'love')

		self.assertEqual(1, press('j'))
		self.assertEqual('love', press('k'))

		self.assertEqual(1, press('40j'))
		self.assertEqual(40, kb.quant)

		km.map('<dir><dir><any><any>', func=move)

		self.assertEqual(1, press('40jkhl'))
		self.assertEqual(40, kb.quant)

	def test_tree_deep_copy(self):
		t = Tree()
		s = t.plow('abcd')
		s.replace('X')
		u = t.copy()
		self.assertEqual(t._tree, u._tree)
		s = t.traverse('abc')
		s.replace('Y')
		self.assertNotEqual(t._tree, u._tree)

	def test_keymanager(self):
		def func(arg):
			return 5
		def getdown(arg):
			return arg.direction.down()

		buffer = KeyBuffer(None, None)
		press = self._mkpress(buffer)
		keymanager = KeyManager(buffer, ['foo', 'bar'])

		map = keymanager.get_context('foo')
		map('a', func)
		map('b', func)
		map = keymanager.get_context('bar')
		map('c', func)
		map('<dir>', getdown)

		keymanager.dir('foo', 'j', down=1)
		keymanager.dir('bar', 'j', down=1)

		keymanager.use_context('foo')
		self.assertEqual(5, press('a'))
		self.assertEqual(5, press('b'))
		self.assertPressFails(buffer, 'c')

		keymanager.use_context('bar')
		self.assertPressFails(buffer, 'a')
		self.assertPressFails(buffer, 'b')
		self.assertEqual(5, press('c'))
		self.assertEqual(1, press('j'))
		keymanager.use_context('foo')
		keymanager.use_context('foo')
		keymanager.use_context('foo')
		keymanager.use_context('bar')
		keymanager.use_context('foo')
		keymanager.use_context('bar')
		keymanager.use_context('bar')
		self.assertEqual(1, press('j'))

	def test_alias_to_direction(self):
		def func(arg):
			return arg.direction.down()

		km = KeyMapWithDirections()
		kb = KeyBuffer(km, km.directions)
		press = self._mkpress(kb)

		km.map('<dir>', func)
		km.map('d<dir>', func)
		km.dir('j', down=42)
		km.dir('k', alias='j')
		self.assertEqual(42, press('j'))

		km.dir('o', alias='j')
		km.dir('ick', alias='j')
		self.assertEqual(42, press('o'))
		self.assertEqual(42, press('dj'))
		self.assertEqual(42, press('dk'))
		self.assertEqual(42, press('do'))
		self.assertEqual(42, press('dick'))
		self.assertPressFails(kb, 'dioo')

	def test_both_directory_and_any_key(self):
		def func(arg):
			return arg.direction.down()
		def func2(arg):
			return "yay"

		km = KeyMap()
		directions = KeyMap()
		kb = KeyBuffer(km, directions)
		press = self._mkpress(kb)

		km.map('abc<dir>', func)
		directions.map('j', dir=Direction(down=42))
		self.assertEqual(42, press('abcj'))

		km.unmap('abc<dir>')

		km.map('abc<any>', func2)
		self.assertEqual("yay", press('abcd'))

		km.map('abc<dir>', func)

		km.map('abc<any>', func2)
		self.assertEqual("yay", press('abcd'))

	def test_map_collision(self):
		def add_dirs(arg):
			return sum(dir.down() for dir in arg.directions)
		def return5(_):
			return 5


		directions = KeyMap()
		directions.map('gg', dir=Direction(down=1))


		km = KeyMap()
		km.map('gh', return5)
		km.map('agh', return5)
		km.map('a<dir>', add_dirs)

		kb = KeyBuffer(km, directions)
		press = self._mkpress(kb, km)

		self.assertEqual(5, press('gh'))
		self.assertEqual(5, press('agh'))
#		self.assertPressFails(kb, 'agh')
		self.assertEqual(1, press('agg'))

	def test_keymap_with_dir(self):
		def func(arg):
			return arg.direction.down()

		km = KeyMapWithDirections()
		kb = KeyBuffer(km, km.directions)

		press = self._mkpress(kb)

		km.map('abc<dir>', func)
		km.dir('j', down=42)
		self.assertEqual(42, press('abcj'))

if __name__ == '__main__': main()
