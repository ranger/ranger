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

from ranger.ext.tree import Tree
from ranger.ext.direction import Direction
from ranger.ext.keybinding_parser import parse_keybinding, DIRKEY, ANYKEY

FUNC = 'func'
DIRARG = 'dir'
ALIASARG = 'alias'

class CommandArgs(object):
	"""
	A CommandArgs object is passed to the keybinding function.

	This object simply aggregates information about the pressed keys
	and the current environment.

	Attributes:
	fm: the FM instance
	wdg: the currently focused widget (or fm, if none is focused)
	keybuffer: the keybuffer object
	n: the prefixed number, eg 5 in the command "5yy"
	directions: a list of directions which are entered for "<dir>"
	direction: the first direction object from that list
	keys: a string representation of the keybuffer
	matches: all keys which are entered for "<any>"
	match: the first match
	binding: the used Binding object
	"""
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
		if hasattr(firstarg, '__call__'):
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
