# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
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

import sys
import copy
import curses.ascii

PY3 = sys.version > '3'
digits = set(range(ord('0'), ord('9')+1))

# Arbitrary numbers which are not used with curses.KEY_XYZ
ANYKEY, PASSIVE_ACTION, ALT_KEY, QUANT_KEY = range(9001, 9005)

special_keys = {
	'bs': curses.KEY_BACKSPACE,
	'backspace': curses.KEY_BACKSPACE,
	'backspace2': curses.ascii.DEL,
	'delete': curses.KEY_DC,
	'insert': curses.KEY_IC,
	'cr': ord("\n"),
	'enter': ord("\n"),
	'return': ord("\n"),
	'space': ord(" "),
	'esc': curses.ascii.ESC,
	'escape': curses.ascii.ESC,
	'down': curses.KEY_DOWN,
	'up': curses.KEY_UP,
	'left': curses.KEY_LEFT,
	'right': curses.KEY_RIGHT,
	'pagedown': curses.KEY_NPAGE,
	'pageup': curses.KEY_PPAGE,
	'home': curses.KEY_HOME,
	'end': curses.KEY_END,
	'tab': ord('\t'),
	's-tab': curses.KEY_BTAB,
}

very_special_keys = {
	'any': ANYKEY,
	'alt': ALT_KEY,
	'bg': PASSIVE_ACTION,
	'allow_quantifiers': QUANT_KEY,
}

for key, val in tuple(special_keys.items()):
	special_keys['a-' + key] = (ALT_KEY, val)

for char in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
	special_keys['a-' + char] = (ALT_KEY, ord(char))

for char in 'abcdefghijklmnopqrstuvwxyz':
	special_keys['c-' + char] = ord(char) - 96

for n in range(64):
	special_keys['f' + str(n)] = curses.KEY_F0 + n

special_keys.update(very_special_keys)
del very_special_keys
reversed_special_keys = dict((v, k) for k, v in special_keys.items())


def parse_keybinding(obj):
	"""
	Translate a keybinding to a sequence of integers

	Example:
	lol<CR>   =>   (ord('l'), ord('o'), ord('l'), ord('\\n'))
	          =>   (108, 111, 108, 10)
	x<A-Left> =>   (120, (27, curses.KEY_LEFT))
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


def construct_keybinding(iterable):
	"""
	Does the reverse of parse_keybinding
	"""
	return ''.join(key_to_string(c) for c in iterable)


def key_to_string(key):
	if key in range(33, 127):
		return chr(key)
	if key in reversed_special_keys:
		return "<%s>" % reversed_special_keys[key]
	return "<%s>" % str(key)


def _unbind_traverse(pointer, keys, pos=0):
	if keys[pos] not in pointer:
		return
	if len(keys) > pos+1 and isinstance(pointer, dict):
		_unbind_traverse(pointer[keys[pos]], keys, pos=pos+1)
		if not pointer[keys[pos]]:
			del pointer[keys[pos]]
	elif len(keys) == pos+1:
		try:
			del pointer[keys[pos]]
			keys.pop()
		except:
			pass

class KeyMaps(dict):
	def __init__(self, keybuffer=None):
		dict.__init__(self)
		self.keybuffer = keybuffer
		self.used_keymap = None

	def use_keymap(self, keymap_name):
		self.keybuffer.keymap = self.get(keymap_name, dict())
		if self.used_keymap != keymap_name:
			self.used_keymap = keymap_name
			self.keybuffer.clear()

	def _clean_input(self, context, keys):
		try:
			pointer = self[context]
		except:
			self[context] = pointer = dict()
		if PY3:
			keys = keys.encode('utf-8').decode('latin-1')
		return list(parse_keybinding(keys)), pointer

	def bind(self, context, keys, leaf):
		keys, pointer = self._clean_input(context, keys)
		if not keys:
			return
		last_key = keys[-1]
		for key in keys[:-1]:
			try:
				if isinstance(pointer[key], dict):
					pointer = pointer[key]
				else:
					pointer[key] = pointer = dict()
			except:
				pointer[key] = pointer = dict()
		pointer[last_key] = leaf

	def copy(self, context, source, target):
		clean_source, pointer = self._clean_input(context, source)
		if not source:
			return
		for key in clean_source:
			try:
				pointer = pointer[key]
			except:
				raise KeyError("Tried to copy the keybinding `%s',"
						" but it was not found." % source)
		self.bind(context, target, copy.deepcopy(pointer))

	def unbind(self, context, keys):
		keys, pointer = self._clean_input(context, keys)
		if not keys:
			return
		_unbind_traverse(pointer, keys)


class KeyBuffer(object):
	any_key             = ANYKEY
	passive_key         = PASSIVE_ACTION
	quantifier_key      = QUANT_KEY
	exclude_from_anykey = [27]

	def __init__(self, keymap=None):
		self.keymap = keymap
		self.clear()

	def clear(self):
		self.keys = []
		self.wildcards = []
		self.pointer = self.keymap
		self.result = None
		self.quantifier = None
		self.finished_parsing_quantifier = False
		self.finished_parsing = False
		self.parse_error = False

		if self.keymap and self.quantifier_key in self.keymap:
			if self.keymap[self.quantifier_key] == 'false':
				self.finished_parsing_quantifier = True

	def add(self, key):
		self.keys.append(key)
		self.result = None
		if not self.finished_parsing_quantifier and key in digits:
			if self.quantifier is None:
				self.quantifier = 0
			self.quantifier = self.quantifier * 10 + key - 48 # (48 = ord(0))
		else:
			self.finished_parsing_quantifier = True

			moved = True
			if key in self.pointer:
				self.pointer = self.pointer[key]
			elif self.any_key in self.pointer and \
					key not in self.exclude_from_anykey:
				self.wildcards.append(key)
				self.pointer = self.pointer[self.any_key]
			else:
				moved = False

			if moved:
				if isinstance(self.pointer, dict):
					if self.passive_key in self.pointer:
						self.result = self.pointer[self.passive_key]
				else:
					self.result = self.pointer
					self.finished_parsing = True
			else:
				self.finished_parsing = True
				self.parse_error = True

	def __str__(self):
		return "".join(key_to_string(c) for c in self.keys)
