class CommandList():
	def __init__(self):
		self.commandlist = []
		self.paths = {}
		self.dummies_in_paths = False
		self.dummy_object = None

	# We need to know when to clear the keybuffer (when a wrong key is pressed)
	# and when to wait for the rest of the key combination. For "gg" we
	# will assign "g" to a dummy which tells the program not to do the latter.
	def rebuild_paths(self):
		""" fill the path dictionary with dummie objects """
		if self.dummies_in_paths:
			self.remove_dummies()
		
		for cmd in self.commandlist:
			for key in cmd.keys:
				for path in self.keypath(key):
					if path not in self.paths:
						self.paths[path] = self.dummy_object

		self.dummies_in_paths = True

	def keypath(self, tup):
		""" split a tuple like (a,b,c,d) into [(a,), (a,b), (a,b,c)] """
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
		""" remove dummie objects in case you have to rebuild a path dictionary which already contains dummie objects. """
		for k in tuple(paths.keys()):
			if paths[k] == self.dummy_object: del paths[k]
		self.dummies_in_paths = False


	def str_to_tuple(self, obj):
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
		""" create a Command object and assign it to the given key combinations. """
		if len(keys) == 0: return

		keys = tuple(map(self.str_to_tuple, keys))

		cmd = Command(fnc, keys)
		cmd.commandlist = self

		self.commandlist.append(cmd)
		for key in keys:
			self.paths[key] = cmd
	
class Command():
	def __init__(self, fnc, keys):
		self.execute = fnc
		self.keys = keys
		self.commandlist = None

#	def execute(self, fm):
#		self.fnc(fm)

