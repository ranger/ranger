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

import curses.ascii
from collections import deque
from string import digits
from ranger.ext.keybinding_parser import parse_keybinding, \
		DIRKEY, ANYKEY, PASSIVE_ACTION
from ranger.container.keymap import Binding, KeyMap # mainly for assertions

MAX_ALIAS_RECURSION = 20

class KeyBuffer(object):
	"""The evaluator and storage for pressed keys"""
	def __init__(self, keymap, direction_keys):
		self.assign(keymap, direction_keys)

	def assign(self, keymap, direction_keys):
		self.keymap = keymap
		self.direction_keys = direction_keys

	def add(self, key):
		assert isinstance(key, int)
		assert key >= 0
		self.all_keys.append(key)
		self.key_queue.append(key)
		while self.key_queue:
			key = self.key_queue.popleft()

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

	def _direction_try_to_finish(self):
		if self.max_alias_recursion <= 0:
			self.failure = True
			return None
		match = self.dir_tree_pointer
		assert isinstance(match, (Binding, dict, KeyMap))
		if isinstance(match, KeyMap):
			self.dir_tree_pointer = self.dir_tree_pointer._tree
			match = self.dir_tree_pointer
		if isinstance(self.dir_tree_pointer, Binding):
			if match.alias:
				self.key_queue.extend(parse_keybinding(match.alias))
				self.dir_tree_pointer = self.direction_keys._tree
				self.max_alias_recursion -= 1
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
		if chr(key) in digits and ANYKEY not in tree:
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
			self.failure = True
			return None
		except KeyError:
			try:
				chr(key) in digits or self.direction_keys._tree[key]
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

	def _try_to_finish(self):
		if self.max_alias_recursion <= 0:
			self.failure = True
			return None
		assert isinstance(self.tree_pointer, (Binding, dict, KeyMap))
		if isinstance(self.tree_pointer, KeyMap):
			self.tree_pointer = self.tree_pointer._tree
		if isinstance(self.tree_pointer, Binding):
			if self.tree_pointer.alias:
				keys = parse_keybinding(self.tree_pointer.alias)
				self.key_queue.extend(keys)
				self.tree_pointer = self.keymap._tree
				self.max_alias_recursion -= 1
			else:
				self.command = self.tree_pointer
				self.done = True

	def clear(self):
		self.max_alias_recursion = MAX_ALIAS_RECURSION
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

		self.key_queue = deque()

		self.eval_quantifier = True
		self.eval_command = True

	def __str__(self):
		"""returns a concatenation of all characters"""
		return "".join("{0:c}".format(c) for c in self.all_keys)
