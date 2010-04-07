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

import curses
from string import ascii_lowercase
from inspect import isfunction, getargspec
from ranger.ext.tree import Tree
from ranger.ext.direction import Direction

MAX_ALIAS_RECURSION = 20
PASSIVE_ACTION = 9003
DIRKEY = 9001
ANYKEY = 9002
FUNC = 'func'
DIRECTION = 'direction'
DIRARG = 'dir'
ALIASARG = 'alias'

def to_string(i):
	"""convert a ord'd integer to a string"""
	try:
		return chr(i)
	except ValueError:
		return '?'

def is_ascii_digit(n):
	return n >= 48 and n <= 57

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
		self.match = keybuffer.matches and keybuffer.matches[0] or None
		self.binding = keybuffer.command

	@staticmethod
	def from_widget(widget):
		return CommandArgs(widget.fm, \
				widget, widget.env.keybuffer)

class KeyMap(Tree):
	"""Contains a tree with all the keybindings"""
	def map(self, *args, **keywords):
		if keywords:
			return self.add_binding(*args, **keywords)
		firstarg = args[-1]
		if isfunction(firstarg):
			keywords[FUNC] = firstarg
			return self.add_binding(*args[:-1], **keywords)
		def decorator_function(func):
			keywords = {FUNC:func}
			self.map(*args, **keywords)
			return func
		return decorator_function

	__call__ = map

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
		try:
			alias = self.actions[ALIASARG]
		except KeyError:
			self.alias = None
		else:
			self.alias = tuple(translate_keys(alias))

class KeyBuffer(object):
	"""The evaluator and storage for pressed keys"""
	def __init__(self, keymap, direction_keys):
		self.assign(keymap, direction_keys)

	def assign(self, keymap, direction_keys):
		self.keymap = keymap
		self.direction_keys = direction_keys

	def add(self, key):
		if self.failure:
			return None
		assert isinstance(key, int)
		assert key >= 0
		self.all_keys.append(key)

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
			self._direction_try_to_finish()

	def _direction_try_to_finish(self, rec=MAX_ALIAS_RECURSION):
		if rec <= 0:
			self.failure = True
			return None
		match = self.dir_tree_pointer
		assert isinstance(match, (Binding, dict, KeyMap))
		if isinstance(match, KeyMap):
			self.dir_tree_pointer = self.dir_tree_pointer._tree
			match = self.dir_tree_pointer
		if isinstance(self.dir_tree_pointer, Binding):
			if match.alias:
				try:
					self.dir_tree_pointer = self.direction_keys[match.alias]
					self._direction_try_to_finish(rec - 1)
				except KeyError:
					self.failure = True
					return None
			else:
				direction = match.actions['dir'].copy()
				if self.direction_quant is not None:
					direction.multiply(self.direction_quant)
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
		assert isinstance(self.tree_pointer, dict), self.tree_pointer
		try:
			self.tree_pointer = self.tree_pointer[key]
		except TypeError:
			print(self.tree_pointer)
			self.failure = True
			return None
		except KeyError:
			try:
				self.tree_pointer = self.tree_pointer[DIRKEY]
			except KeyError:
				try:
					self.tree_pointer = self.tree_pointer[ANYKEY]
				except KeyError:
					self.failure = True
					return None
				else:
					self.matches.append(key)
					assert isinstance(self.tree_pointer, (Binding, dict))
					self._try_to_finish()
			else:
				assert isinstance(self.tree_pointer, (Binding, dict))
				self.eval_command = False
				self.eval_quantifier = True
				self.dir_tree_pointer = self.direction_keys._tree
		else:
			if isinstance(self.tree_pointer, dict):
				try:
					self.command = self.tree_pointer[PASSIVE_ACTION]
				except (KeyError, TypeError):
					self.command = None
			self._try_to_finish()

	def _try_to_finish(self, rec=MAX_ALIAS_RECURSION):
		if rec <= 0:
			self.failure = True
			return None
		assert isinstance(self.tree_pointer, (Binding, dict, KeyMap))
		if isinstance(self.tree_pointer, KeyMap):
			self.tree_pointer = self.tree_pointer._tree
		if isinstance(self.tree_pointer, Binding):
			if self.tree_pointer.alias:
				try:
					self.tree_pointer = self.keymap[self.tree_pointer.alias]
					self._try_to_finish(rec - 1)
				except KeyError:
					self.failure = True
					return None
			else:
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
		for char in translate_keys(string):
			self.add(char)
			if self.done:
				return self.command
			if self.failure:
				break
		return self.command

special_keys = {
	'dir': DIRKEY,
	'any': ANYKEY,
	'bg': PASSIVE_ACTION,
	'cr': ord("\n"),
	'enter': ord("\n"),
	'space': ord(" "),
	'down': curses.KEY_DOWN,
	'up': curses.KEY_UP,
	'left': curses.KEY_LEFT,
	'right': curses.KEY_RIGHT,
	'mouse': curses.KEY_MOUSE,
	'resize': curses.KEY_RESIZE,
	'pagedown': curses.KEY_NPAGE,
	'pageup': curses.KEY_PPAGE,
	'home': curses.KEY_HOME,
	'end': curses.KEY_END,
	'tab': ord('\t'),
}
for char in ascii_lowercase:
	special_keys['c-' + char] = ord(char) - 96
	special_keys['a-' + char] = (27, ord(char))

def translate_keys(obj):
	"""
	Translate a keybinding to a sequence of integers

	Example:
	lol<CR>   =>   (108, 111, 108, 10)
	"""
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
						keys = special_keys[string]
						for key in keys:
							yield key
					except KeyError:
						yield ord('<')
						for c in bracket_content:
							yield ord(c)
						yield ord('>')
					except TypeError:
						yield keys  # it was no tuple, just an int
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
