if __name__ == '__main__': from __init__ import init; init()
from unittest import TestCase, main
from pprint import pprint as print

from inspect import isfunction, getargspec
import inspect
from sys import intern

FUNC = 'func'
DIRECTION = 'direction'
DIRKEY = 9001
ANYKEY = 9002
QUANTIFIER = 'n'
MATCH = intern('!!')

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

class CommandArgs(object):
	"""The arguments which are passed to a keybinding function"""
	def __init__(self, fm, widget, keybuffer):
		self.fm = fm
		self.wdg = widget
		self.keybuffer = keybuffer
		self.n = keybuffer.quant1
		self.direction = keybuffer.direction
		self.keys = str(keybuffer)
		self.moo = keybuffer.moo

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

		# evaluate first quantifier
		if self.level == 0:
			if is_ascii_digit(key) and ANYKEY not in self.tree_pointer:
				if self.quant1 is None:
					self.quant1 = 0
				self.quant1 = self.quant1 * 10 + key - 48
			else:
				self.level = 1

		# evaluate the command and the second quantifier.
		# it's possible to jump between them. "x3xj" is equivalent to "xx3j"
		if self.level == 1:
			try:
				self.tree_pointer = self.tree_pointer[key]
			except TypeError:
				self.failure = True
				return None
			except KeyError:
				if is_ascii_digit(key) and ANYKEY not in self.tree_pointer:
					if self.quant2 is None:
						self.quant2 = 0
					self.quant2 = self.quant2 * 10 + key - 48
				elif DIRKEY in self.tree_pointer:
					self.level = 2
					self.command = self.tree_pointer[DIRKEY]
					self.tree_pointer = self.direction_keys._tree
				elif ANYKEY in self.tree_pointer:
					self.moo.append(key)
					self.tree_pointer = self.tree_pointer[ANYKEY]
					self._try_to_finish()
				else:
					self.failure = True
					return None
			else:
				self._try_to_finish()

		# evaluate direction keys {j,k,gg,pagedown,...}
		if self.level == 2:
			try:
				self.tree_pointer = self.tree_pointer[key]
			except KeyError:
				self.failure = True
			else:
				if not isinstance(self.tree_pointer, dict):
					match = self.tree_pointer
					self.direction = match.actions['dir'] * self.quant2
					self.done = True

	def _try_to_finish(self):
		if not isinstance(self.tree_pointer, dict):
			match = self.tree_pointer
			self.command = match
			if not match.has_direction:
				if self.quant2 is not None:
					self.direction = self.direction * self.quant2
				self.done = True

	def clear(self):
		self.failure = False
		self.done = False
		self.quant1 = None
		self.moo = []
		self.quant2 = None
		self.command = None
		self.direction = Direction(down=1)
		self.all_keys = []
		self.tree_pointer = self.keymap._tree
		self.direction_tree_pointer = self.direction_keys._tree
		self.level = 0
		# level 0 = parsing quantifier 1
		#       1 = parsing command or quantifier 2
		#       2 = parsing direction

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
		else:
			raise TypeError(key)

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
	def fnc(n=None):
		if n is None:
			return value
		return n
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

class Test(TestCase):
	"""The test cases"""
	def _mkpress(self, keybuffer, keymap):
		def press(keys):
			keybuffer.clear()
			match = keybuffer.simulate_press(keys)
			self.assertFalse(keybuffer.failure,
					"parsing keys '"+keys+"' did fail!")
			self.assertTrue(keybuffer.done,
					"parsing keys '"+keys+"' did not complete!")
			arg = CommandArgs(None, None, keybuffer)
			return match.function(arg)
		return press

	def test_add(self):
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
		km.add(n(5), 'd')
		match = kb.simulate_press('3d')
		self.assertEqual(3, match.function(kb.quant1))
		kb.clear()
		match = kb.simulate_press('6223d')
		self.assertEqual(6223, match.function(kb.quant1))
		kb.clear()

	def test_direction(self):
		km = Keymap()
		directions = Keymap()
		kb = KeyBuffer(km, directions)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))
		km.add(nd, 'd}')
		km.add('dd', func=nd, with_direction=False)

		press = self._mkpress(kb, km)

		self.assertEqual(  3, press('3ddj'))
		self.assertEqual( 15, press('3d5j'))
		self.assertEqual(-15, press('3d5k'))
		self.assertEqual( 15, press('3d5d'))
		self.assertEqual(  3, press('3dd'))
		self.assertEqual(  1, press('dd'))

		km.add(nd, 'x}')
		km.add('xxxx', func=nd, with_direction=False)

		self.assertEqual(1, press('xxxxj'))
		self.assertEqual(1, press('xxxxjsomeinvalitchars'))

		# these combinations should break:
		kb.clear()
		self.assertEqual(None, kb.simulate_press('xxxj'))
		kb.clear()
		self.assertEqual(None, kb.simulate_press('xxj'))
		kb.clear()
		self.assertEqual(None, kb.simulate_press('xxkldfjalksdjklsfsldkj'))
		kb.clear()
		self.assertEqual(None, kb.simulate_press('xyj'))
		kb.clear()
		self.assertEqual(None, kb.simulate_press('x'))  #direction missing
		kb.clear()

	def test_any_key(self):
		km = Keymap()
		directions = Keymap()
		kb = KeyBuffer(km, directions)
		directions.add('j', dir=Direction(down=1))
		directions.add('k', dir=Direction(down=-1))

		def cat(arg):
			n = arg.n is None and 1 or arg.n
			return ''.join(chr(c) for c in arg.moo) * n

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

if __name__ == '__main__': main()
