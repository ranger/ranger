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
		for k in tuple(paths.keys()):
			if paths[k] == self.dummy_object: del paths[k]
		self.dummies_in_paths = False


	def _str_to_tuple(self, obj):
		"""splits a string into a tuple of integers"""
		if isinstance(obj, tuple):
			return obj
		elif isinstance(obj, str):
			return tuple(map(ord, list(obj)))
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
		for key in keys:
			self.paths[key] = cmd
	
	def hint(self, text, *keys):
		"""create a Hint object and assign it to the given key combinations."""
		if len(keys) == 0: return

		keys = tuple(map(self._str_to_tuple, keys))

		obj = Hint(text, keys)

		self.commandlist.append(obj)
		for key in keys:
			self.paths[key] = obj

	
class Command(object):
	"""Command objects store information about a command"""

	keys = []

	def __init__(self, fnc, keys):
		self.keys = keys
		self.execute = fnc
	
	def execute(self, *args):
		"""Execute the command"""
	
	def execute_wrap(self, displayable):
		self.execute(cmdarg(displayable))
	
#	def __str__(self):
#		return 'Cmd({0})'.format(str(self.keys))

class Hint(object):
	"""Hints display text without clearing the keybuffer"""

	keys = []
	text = ''

	def __init__(self, text, keys):
		self.keys = keys
		self.text = text

#	def __str__(self):
#		return 'Hint({0})'.format(str(self.keys))
