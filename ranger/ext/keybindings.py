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

from ranger.ext.keybinding_parser import (parse_keybinding,
	ANYKEY, PASSIVE_ACTION, QUANT_KEY)
import sys
import copy

PY3 = sys.version > '3'

digits = set(range(ord('0'), ord('9')+1))

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

	def bind(self, context, keys, leaf):
		try:
			pointer = self[context]
		except:
			self[context] = pointer = dict()
		if PY3:
			keys = keys.encode('utf-8').decode('latin-1')
		keys = list(parse_keybinding(keys))
		if not keys:
			return
		last_key = keys[-1]
		for key in keys[:-1]:
			try:
				pointer = pointer[key]
			except:
				pointer[key] = pointer = dict()
		pointer[last_key] = leaf

	def copy(self, context, source, target):
		try:
			pointer = self[context]
		except:
			self[context] = pointer = dict()
		if PY3:
			source = source.encode('utf-8').decode('latin-1')
		source = list(parse_keybinding(source))
		if not source:
			return

		for key in source:
			pointer = pointer[key]
		self.bind(context, target, copy.deepcopy(pointer))


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
		return "".join("{0:c}".format(c) for c in self.keys)
