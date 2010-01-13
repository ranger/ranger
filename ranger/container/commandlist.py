# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

class CommandArgument(object):
	def __init__(self, fm, displayable, keybuffer):
		self.fm = fm
		self.wdg = displayable
		self.keybuffer = keybuffer
		self.n = keybuffer.number
		self.keys = str(keybuffer)

def cmdarg(displayable):
	return CommandArgument(displayable.fm, \
			displayable, displayable.env.keybuffer)

class CommandList(object):
	"""
	CommandLists are dictionary-like objects which give you a command
	for a given key combination.  CommandLists must be filled before use.
	"""

	dummy_object = None
	dummies_in_paths = False
	paths = {}
	commandlist = []

	def __init__(self):
		self.commandlist = []
		self.paths = {}
	
	def __getitem__(self, key):
		"""Returns the command with the given key combination"""
		if isinstance(key, str):
			key = self._str_to_tuple(key)
		return self.paths[key]

	def rebuild_paths(self):
		"""
		Fill the path dictionary with dummie objects.
		We need to know when to clear the keybuffer (when a wrong key is pressed)
		and when to wait for the rest of the key combination.  For "gg" we
		will assign "g" to a dummy which tells the program to do the latter
		and wait.
		"""
		if self.dummies_in_paths:
			self.remove_dummies()

		for cmd in self.commandlist:
			for key in cmd.keys:
				for path in self._keypath(key):
					if path not in self.paths:
						self.paths[path] = self.dummy_object

		self.dummies_in_paths = True

	def _keypath(self, tup):
		"""split a tuple like (a,b,c,d) into [(a,), (a,b), (a,b,c)]"""
		length = len(tup)

		if length == 0:
			return ()
		if length == 1:
			return (tup, )

		current = []
		all = []
		
		for i in range(len(tup) - 1):
			current.append(tup[i])
			all.append(tuple(current))

		return all

	def remove_dummies(self):
		"""
		Remove dummie objects in case you have to rebuild a path dictionary
		which already contains dummie objects.
		"""
		for k in tuple(self.paths.keys()):
			if self.paths[k] == self.dummy_object: del self.paths[k]
		self.dummies_in_paths = False


	def _str_to_tuple(self, obj):
		"""splits a string into a tuple of integers"""
		if isinstance(obj, tuple):
			return obj
		elif isinstance(obj, str):
			return tuple(map(ord, obj))
		elif isinstance(obj, int):
			return (obj, )
		else:
			raise TypeError('need a str, int or tuple for str_to_tuple')
	
	def bind(self, fnc, *keys):
		"""create a Command object and assign it to the given key combinations."""
		if len(keys) == 0: return

		keys = tuple(map(self._str_to_tuple, keys))

		cmd = Command(fnc, keys)

		self.commandlist.append(cmd)
		for key in cmd.keys:
			self.paths[key] = cmd
	
	def hint(self, text, *keys):
		"""create a Hint object and assign it to the given key combinations."""
		if len(keys) == 0: return

		keys = tuple(map(self._str_to_tuple, keys))

		obj = Hint(text, keys)

		self.commandlist.append(obj)
		for key in obj.keys:
			self.paths[key] = obj
	
	def alias(self, existing, *new):
		"""bind the <new> keys to the command of the <existing> key"""
		existing = self._str_to_tuple(existing)
		new = tuple(map(self._str_to_tuple, new))

		obj = AliasedCommand(_make_getter(self.paths, existing), new)

		self.commandlist.append(obj)
		for key in new:
			self.paths[key] = obj

	def unbind(self, *keys):
		i = len(self.commandlist)
		keys = set(map(self._str_to_tuple, keys))

		while i > 0:
			i -= 1
			cmd = self.commandlist[i]
			cmd.keys -= keys
			if not cmd.keys:
				del self.commandlist[i]

		for k in keys:
			del self.paths[k]

	def clear(self):
		"""remove all bindings"""
		self.paths.clear()
		del self.commandlist[:]
	

class Command(object):
	"""Command objects store information about a command"""

	keys = []

	def __init__(self, fnc, keys):
		self.keys = set(keys)
		self.execute = fnc
	
	def execute(self, *args):
		"""Execute the command"""
	
	def execute_wrap(self, displayable):
		self.execute(cmdarg(displayable))
	
#	def __str__(self):
#		return 'Cmd({0})'.format(str(self.keys))

class AliasedCommand(Command):
	def __init__(self, getter, keys):
		self.getter = getter
		self.keys = set(keys)

	def get_execute(self):
		return self.getter()

	execute = property(get_execute)

class Hint(object):
	"""Hints display text without clearing the keybuffer"""

	keys = []
	text = ''

	def __init__(self, text, keys):
		self.keys = set(keys)
		self.text = text

#	def __str__(self):
#		return 'Hint({0})'.format(str(self.keys))

def _make_getter(paths, key):
	def getter():
		try:
			return paths[key].execute
		except:
			return lambda: None
	return getter
