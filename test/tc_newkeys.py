# coding=utf-8
if __name__ == '__main__': from __init__ import init; init()
from unittest import TestCase, main

from inspect import isfunction, getargspec
import inspect
import sys
from string import ascii_lowercase
try:
	from sys import intern
except:
	pass

FUNC = 'func'
DIRECTION = 'direction'
DIRARG = 'dir'
DIRKEY = 9001
ANYKEY = 9002

def to_string(i):
	"""convert a ord'd integer to a string"""
	try:
		return chr(i)
	except ValueError:
		return '?'

def is_ascii_digit(n):
	return n >= 48 and n <= 57

class Direction(object):
	"""An object with a down and right method"""
	def __init__(self, down=0, right=0):
		self.down = down
		self.right = right

	def copy(self):
		new = type(self)()
		new.__dict__.update(self.__dict__)
		return new

	def __mul__(self, other):
		copy = self.copy()
		if other is not None:
			copy.down *= other
			copy.right *= other
		return copy
	__rmul__ = __mul__

class CommandArgs(object):
	"""The arguments which are passed to a keybinding function"""
	def __init__(self, fm, widget, keybuffer):
		self.fm = fm
		self.wdg = widget
		self.keybuffer = keybuffer
		self.n = keybuffer.quant
		self.direction = keybuffer.directions and keybuffer.directions[0] or None
		self.directions = keybuffer.directions
		self.keys = str(keybuffer)
		self.matches = keybuffer.matches
		self.binding = keybuffer.command

class KeyBuffer(object):
	"""The evaluator and storage for pressed keys"""
	def __init__(self, keymap, direction_keys):
		self.keymap = keymap
		self.direction_keys = direction_keys
		self.clear()

	def add(self, key):
		if self.failure:
			return None
		assert isinstance(key, int)
		assert key >= 0

		# evaluate quantifiers
		if self.eval_quantifier and self._do_eval_quantifier(key):
			return

		# evaluate the command
		if self.eval_command and self._do_eval_command(key):
			return

		# evaluate (the first number of) the direction-quantifier
		if self.eval_quantifier and self._do_eval_quantifier(key):
			return

		# evaluate direction keys {j,k,gg,pagedown,...}
		if not self.eval_command:
			self._do_eval_direction(key)

	def _do_eval_direction(self, key):
		# swap quant and direction_quant in bindings like '<dir>'
		if self.quant is not None and self.command is None \
		and self.direction_quant is None:
			self.direction_quant = self.quant
			self.quant = None

		try:
			assert isinstance(self.dir_tree_pointer, dict)
			self.dir_tree_pointer = self.dir_tree_pointer[key]
		except KeyError:
			self.failure = True
		else:
			if not isinstance(self.dir_tree_pointer, dict):
				match = self.dir_tree_pointer
				assert isinstance(match, Binding)
				direction = match.actions['dir'] * self.direction_quant
				self.directions.append(direction)
				self.direction_quant = None
				self.eval_command = True
				self._try_to_finish()

	def _do_eval_quantifier(self, key):
		if self.eval_command:
			tree = self.tree_pointer
		else:
			tree = self.dir_tree_pointer
		if is_ascii_digit(key) and ANYKEY not in tree:
			attr = self.eval_command and 'quant' or 'direction_quant'
			if getattr(self, attr) is None:
				setattr(self, attr, 0)
			setattr(self, attr, getattr(self, attr) * 10 + key - 48)
		else:
			self.eval_quantifier = False
			return None
		return True

	def _do_eval_command(self, key):
		try:
			assert isinstance(self.tree_pointer, dict)
			self.tree_pointer = self.tree_pointer[key]
		except TypeError:
			print(self.tree_pointer)
			self.failure = True
			return None
		except KeyError:
			if DIRKEY in self.tree_pointer:
				self.eval_command = False
				self.eval_quantifier = True
				self.tree_pointer = self.tree_pointer[DIRKEY]
				assert isinstance(self.tree_pointer, (Binding, dict))
				self.dir_tree_pointer = self.direction_keys._tree
			elif ANYKEY in self.tree_pointer:
				self.matches.append(key)
				self.tree_pointer = self.tree_pointer[ANYKEY]
				assert isinstance(self.tree_pointer, (Binding, dict))
				self._try_to_finish()
			else:
				self.failure = True
				return None
		else:
			self._try_to_finish()

	def _try_to_finish(self):
		assert isinstance(self.tree_pointer, (Binding, dict))
		if not isinstance(self.tree_pointer, dict):
			self.command = self.tree_pointer
			self.done = True

	def clear(self):
		self.failure = False
		self.done = False
		self.quant = None
		self.matches = []
		self.command = None
		self.direction_quant = None
		self.directions = []
		self.all_keys = []
		self.tree_pointer = self.keymap._tree
		self.dir_tree_pointer = self.direction_keys._tree

		self.eval_quantifier = True
		self.eval_command = True

	def __str__(self):
		"""returns a concatenation of all characters"""
		return "".join(to_string(c) for c in self.all_keys)

	def simulate_press(self, string):
		for char in string:
			self.add(ord(char))
			if self.done:
				return self.command
			if self.failure:
				break

key_map = {
	'dir': DIRKEY,
	'any': ANYKEY,
	'cr': ord("\n"),
	'enter': ord("\n"),
	'space': ord(" "),
	'space': ord(" "),
	'tab': ord('\t'),
}
for char in ascii_lowercase:
	key_map['c-' + char] = ord(char) - 96

def translate_keys(obj):
	assert isinstance(obj, (tuple, int, str))
	if isinstance(obj, tuple):
		for char in obj:
			yield char
	elif isinstance(obj, int):
		yield obj
	elif isinstance(obj, str):
		in_brackets = False
		bracket_content = None
		for char in obj:
			if in_brackets:
				if char == '>':
					in_brackets = False
					string = ''.join(bracket_content).lower()
					try:
						yield key_map[string]
					except KeyError:
						yield ord('<')
						for c in bracket_content:
							yield ord(c)
						yield ord('>')
				else:
					bracket_content.append(char)
			else:
				if char == '<':
					in_brackets = True
					bracket_content = []
				else:
					yield ord(char)
		if in_brackets:
			yield ord('<')
			for c in bracket_content:
				yield ord(c)

class Tree(object):
	def __init__(self, dictionary=None, parent=None, key=None):
		assert dictionary is None or isinstance(dictionary, dict)
		if dictionary is None:
			self._tree = dict()
		else:
			self._tree = dictionary
		self.key = key
		self.parent = parent

	def set(self, keys, value, force=True):
		"""Sets the element at the end of the path to <value>."""
		if not isinstance(keys, (list, tuple)):
			keys = tuple(keys)
		if len(keys) == 0:
			self.replace(value)
		else:
			fnc = force and self.plow or self.traverse
			subtree = fnc(keys)
			subtree.replace(value)

	def replace(self, value):
		if self.parent:
			self.parent[self.key] = value
		self._tree = value

	def plow(self, iterable):
		"""Move along a path, creating nonexistant subtrees"""
		tree = self._tree
		last_tree = None
		char = None
		for char in iterable:
			try:
				newtree = tree[char]
				if not isinstance(newtree, dict):
					raise KeyError()
			except KeyError:
				newtree = dict()
				tree[char] = newtree
			last_tree = tree
			tree = newtree
		if isinstance(tree, dict):
			return Tree(tree, parent=last_tree, key=char)
		else:
			return tree

	def traverse(self, iterable):
		"""Move along a path, raising exceptions when failed"""
		tree = self._tree
		last_tree = tree
		char = None
		for char in iterable:
			last_tree = tree
			try:
				tree = tree[char]
			except TypeError:
				raise KeyError("trying to enter leaf")
			except KeyError:
				raise KeyError(str(char) + " not in tree " + str(tree))
		if isinstance(tree, dict):
			return Tree(tree, parent=last_tree, key=char)
		else:
			return tree


class KeyMap(Tree):
	"""Contains a tree with all the keybindings"""
	def add(self, *args, **keywords):
		if keywords:
			return self.add_binding(*args, **keywords)
		firstarg = args[0]
		if isfunction(firstarg):
			keywords[FUNC] = firstarg
			return self.add_binding(*args[1:], **keywords)
		def decorator_function(func):
			keywords = {FUNC:func}
			self.add(*args, **keywords)
			return func
		return decorator_function

	def add_binding(self, *keys, **actions):
		assert keys
		bind = Binding(keys, actions)
		for key in keys:
			self.set(translate_keys(key), bind)

	def __getitem__(self, key):
		return self.traverse(translate_keys(key))

class Binding(object):
	"""The keybinding object"""
	def __init__(self, keys, actions):
		assert hasattr(keys, '__iter__')
		assert isinstance(actions, dict)
		self.actions = actions
		try:
			self.function = self.actions[FUNC]
		except KeyError:
			self.function = None
			self.has_direction = False
		else:
			argnames = getargspec(self.function)[0]
			try:
				self.has_direction = actions['with_direction']
			except KeyError:
				self.has_direction = DIRECTION in argnames
		try:
			self.direction = self.actions[DIRARG]
		except KeyError:
			self.direction = None


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
			self.assert_(match.function, match.__dict__)
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
		test('k<a')
		test('k<anz>')
		test('k<a<nz>')
		test('k<a<nz>')
		test('k<a<>nz>')
		test('>nz>')

	def test_tree(self):
		t = Tree()
		t.set('abcd', "Yes")
		self.assertEqual("Yes", t.traverse('abcd'))
		self.assertRaises(KeyError, t.traverse, 'abcde')
		self.assertRaises(KeyError, t.traverse, 'xyz')
		self.assert_(isinstance(t.traverse('abc'), Tree))

		t2 = Tree()
		self.assertRaises(KeyError, t2.set, 'axy', "Lol", force=False)
		subtree = t2.set('axy', "Lol")
		self.assertEqual("Yes", t.traverse('abcd'))
		self.assertRaises(KeyError, t2.traverse, 'abcd')
		self.assertEqual("Lol", t2.traverse('axy'))

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
		directions.add('k', dir=Direction(down=-1))
		km.add('<dir>', func=move)

		self.assertEqual(1, press('j'))
		self.assertEqual(-1, press('k'))

		km.add('k', func=lambda _: 'love')

		self.assertEqual(1, press('j'))
		self.assertEqual('love', press('k'))

		self.assertEqual(40, press('40j'))

		km.add('<dir><dir><any><any>', func=move)

		self.assertEqual(40, press('40jkhl'))


if __name__ == '__main__': main()
