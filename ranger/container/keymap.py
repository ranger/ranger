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
from inspect import isfunction, getargspec
from ranger.ext.tree import Tree
from ranger.ext.direction import Direction
from ranger.ext.keybinding_parser import parse_keybinding, \
		DIRKEY, ANYKEY, PASSIVE_ACTION

MAX_ALIAS_RECURSION = 20
FUNC = 'func'
DIRARG = 'dir'
ALIASARG = 'alias'

class CommandArgs(object):
	"""The arguments which are passed to a keybinding function"""
	def __init__(self, fm, widget, keybuf):
		self.fm = fm
		self.wdg = widget
		self.keybuffer = keybuf
		self.n = keybuf.quant
		self.direction = keybuf.directions and keybuf.directions[0] or None
		self.directions = keybuf.directions
		self.keys = str(keybuf)
		self.matches = keybuf.matches
		self.match = keybuf.matches and keybuf.matches[0] or None
		self.binding = keybuf.command

	@staticmethod
	def from_widget(widget):
		return CommandArgs(widget.fm, \
				widget, widget.env.keybuffer)

class KeyMap(Tree):
	"""Contains a tree with all the keybindings"""
	def map(self, *args, **keywords):
		if keywords:
			return self._add_binding(*args, **keywords)
		firstarg = args[-1]
		if isfunction(firstarg):
			keywords[FUNC] = firstarg
			return self._add_binding(*args[:-1], **keywords)
		def decorator_function(func):
			keywords = {FUNC:func}
			self.map(*args, **keywords)
			return func
		return decorator_function

	__call__ = map

	def _add_binding(self, *keys, **actions):
		assert keys
		bind = Binding(keys, actions)
		for key in keys:
			self.set(parse_keybinding(key), bind)

	def unmap(self, *keys):
		for key in keys:
			self.unset(parse_keybinding(key))

	def __getitem__(self, key):
		return self.traverse(parse_keybinding(key))


class KeyMapWithDirections(KeyMap):
	def __init__(self, *args, **keywords):
		Tree.__init__(self, *args, **keywords)
		self.directions = KeyMap()

	def merge(self, other):
		assert hasattr(other, 'directions'), 'Merging with wrong type?'
		Tree.merge(self, other)
		Tree.merge(self.directions, other.directions)

	def dir(self, *args, **keywords):
		if ALIASARG in keywords:
			self.directions.map(*args, **keywords)
		else:
			self.directions.map(*args, dir=Direction(**keywords))


class KeyManager(object):
	def __init__(self, keybuffer, contexts):
		self._keybuffer = keybuffer
		self._list_of_contexts = contexts
		self.clear()

	def clear(self):
		self.contexts = dict()
		for context in self._list_of_contexts:
			self.contexts[context] = KeyMapWithDirections()

	def map(self, context, *args, **keywords):
		self.get_context(context).map(*args, **keywords)

	def dir(self, context, *args, **keywords):
		self.get_context(context).dir(*args, **keywords)

	def unmap(self, context, *args, **keywords):
		self.get_context(context).unmap(*args, **keywords)

	def merge_all(self, keymapwithdirection):
		for context, keymap in self.contexts.items():
			keymap.merge(keymapwithdirection)

	def get_context(self, context):
		assert isinstance(context, str)
		assert context in self.contexts, "no such context: " + context
		return self.contexts[context]
	__getitem__ = get_context

	def use_context(self, context):
		context = self.get_context(context)
		if self._keybuffer.keymap is not context:
			self._keybuffer.assign(context, context.directions)
			self._keybuffer.clear()


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
		try:
			self.direction = self.actions[DIRARG]
		except KeyError:
			self.direction = None
		try:
			alias = self.actions[ALIASARG]
		except KeyError:
			self.alias = None
		else:
			self.alias = tuple(parse_keybinding(alias))

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
