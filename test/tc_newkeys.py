# coding=utf-8
if __name__ == '__main__': from __init__ import init; init()
from unittest import TestCase, main
#from pprint import pprint as print

from inspect import isfunction, getargspec
import inspect
try:
	from sys import intern
except:
	pass

FUNC = 'func'
DIRECTION = 'direction'
DIRKEY = 9001
ANYKEY = 9002
QUANTIFIER = 'n'

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
		try:
			assert isinstance(self.dir_tree_pointer, dict)
			self.dir_tree_pointer = self.dir_tree_pointer[key]
		except KeyError:
			self.failure = True
		else:
			if not isinstance(self.dir_tree_pointer, dict):
				match = self.dir_tree_pointer
				assert isinstance(match, binding)
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
				assert isinstance(self.tree_pointer, (binding, dict))
				self.dir_tree_pointer = self.direction_keys._tree
			elif ANYKEY in self.tree_pointer:
				self.matches.append(key)
				self.tree_pointer = self.tree_pointer[ANYKEY]
				assert isinstance(self.tree_pointer, (binding, dict))
				self._try_to_finish()
			else:
				self.failure = True
				return None
		else:
			self._try_to_finish()

	def _try_to_finish(self):
		assert isinstance(self.tree_pointer, (binding, dict))
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

class Keymap(object):
	"""Contains a tree with all the keybindings"""
	def __init__(self):
		self._tree = dict()

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

	def _split(self, key):
		assert isinstance(key, (tuple, int, str))
		if isinstance(key, tuple):
			for char in key:
					yield char
		elif isinstance(key, str):
			for char in key:
				if char == '.':
					yield ANYKEY
				elif char == '}':
					yield DIRKEY
				else:
					yield ord(char)
		elif isinstance(key, int):
			yield key

	def add_binding(self, *keys, **actions):
		assert keys
		bind = binding(keys, actions)

		for key in keys:
			assert key
			chars = tuple(self._split(key))
			tree = self.traverse_tree(chars[:-1])
			if isinstance(tree, dict):
				tree[chars[-1]] = bind

	def traverse_tree(self, generator):
		tree = self._tree
		for char in generator:
			try:
				tree = tree[char]
			except KeyError:
				tree[char] = dict()
				tree = tree[char]
			except TypeError:
				raise TypeError("Attempting to override existing entry")
		return tree

	def __getitem__(self, key):
		tree = self._tree
		for char in self._split(key):
			try:
				tree = tree[char]
			except TypeError:
				raise KeyError("trying to enter leaf")
			except KeyError:
				raise KeyError(str(char) + " not in tree " + str(tree))
		try:
			return tree
		except KeyError:
			raise KeyError(str(char) + " not in tree " + str(tree))

class binding(object):
	"""The keybinding object"""
	def __init__(self, keys, actions):
		assert hasattr(keys, '__iter__')
		assert isinstance(actions, dict)
		self.keys = set(keys)
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

	def add_keys(self, keys):
		assert isinstance(keys, set)
		self.keys |= keys

	def has(self, action):
		return action in self.actions

	def action(self, key):
		return self.actions[key]

def n(value):
	""" return n or value """
	def fnc(arg=None):
		if arg is None or arg.n is None:
			return value
		return arg.n
	return fnc

def nd(arg):
	""" n * direction """
	if arg.n is None:
		n = 1
	else:
		n = arg.n
	if arg.direction is None:
		dir = Direction(down=1)
	else:
		dir = arg.direction
	return n * dir.down

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
	def test_add(self):
		# depends on internals
		c = Keymap()
		c.add(lambda *_: 'lolz', 'aa', 'b')
		self.assert_(c['aa'].actions[FUNC](), 'lolz')
		@c.add('a', 'c')
		def test():
			return 5
		self.assert_(c['b'].actions[FUNC](), 'lolz')
		self.assert_(c['c'].actions[FUNC](), 5)
		self.assert_(c['a'].actions[FUNC](), 5)

	def test_quantifier(self):
		km = Keymap()
		directions = Keymap()
		kb = KeyBuffer(km, directions)
		km.add(n(5), 'p')
		press = self._mkpress(kb, km)
		self.assertEqual(3, press('3p'))
		self.assertEqual(6223, press('6223p'))

	def test_direction(self):
		km = Keymap()
		directions = Keymap()
		kb = KeyBuffer(km, directions)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))
		km.add(nd, 'd}')
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

		km.add(nd, 'x}')
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
		km = Keymap()
		directions = Keymap()
		kb = KeyBuffer(km, directions)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))

		def cat(arg):
			n = arg.n is None and 1 or arg.n
			return ''.join(chr(c) for c in arg.matches) * n

		km.add(cat, 'return.')
		km.add(cat, 'cat4....')

		press = self._mkpress(kb, km)

		self.assertEqual('x', press('returnx'))
		self.assertEqual('abcd', press('cat4abcd'))
		self.assertEqual('abcdabcd', press('2cat4abcd'))
		self.assertEqual('55555', press('5return5'))

		km.add(lambda _: Ellipsis, '.')
		self.assertEqual('x', press('returnx'))
		self.assertEqual('abcd', press('cat4abcd'))
		self.assertEqual(Ellipsis, press('2cat4abcd'))
		self.assertEqual(Ellipsis, press('5return5'))
		self.assertEqual(Ellipsis, press('f'))
		self.assertEqual(Ellipsis, press('ß'))
		self.assertEqual(Ellipsis, press('ア'))
		self.assertEqual(Ellipsis, press('9'))

	def test_multiple_directions(self):
		km = Keymap()
		directions = Keymap()
		kb = KeyBuffer(km, directions)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))

		def add_dirs(arg):
			n = 0
			for dir in arg.directions:
				n += dir.down
			return n

		km.add(add_dirs, 'x}y}')
		km.add(add_dirs, 'four}}}}')

		press = self._mkpress(kb, km)

		self.assertEqual(2, press('xjyj'))
		self.assertEqual(0, press('fourjkkj'))
		self.assertEqual(2, press('four2j4k2j2j'))
		self.assertEqual(10, press('four1j2j3j4j'))
		self.assertEqual(10, press('four1j2j3j4jafslkdfjkldj'))

	def test_corruptions(self):
		km = Keymap()
		directions = Keymap()
		kb = KeyBuffer(km, directions)
		press = self._mkpress(kb, km)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))
		km.add('xxx', func=lambda _: 1)

		self.assertEqual(1, press('xxx'))

		# corrupt the tree
		tup = tuple(km._split('xxx'))
		subtree = km.traverse_tree(tup[:-1])
		subtree[tup[-1]] = "Boo"

		self.assertPressFails(kb, 'xxy')
		self.assertPressFails(kb, 'xzy')
		self.assertPressIncomplete(kb, 'xx')
		self.assertPressIncomplete(kb, 'x')
		self.assertRaises(AssertionError, kb.simulate_press, 'xxx')
		kb.clear()

if __name__ == '__main__': main()
