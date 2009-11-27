class CommandDummy():
	pass

class CommandList():
	def __init__(self):
		self.commandlist = []
		self.paths = {}
		self.dummies_in_paths = False
		self.dummy_object = CommandDummy

	def rebuild_paths(self):
		paths = self.paths

		if self.dummies_in_paths:
			self.remove_dummies()
		
		for cmd in self.commandlist:
			for key in cmd.keys:
				path = []
				for path in self.keypath(key):
					try: paths[path]
					except KeyError:
						paths[path] = self.dummy_object

		self.dummies_in_paths = True

	def keypath(self, tup):
		current = []
		all = []
		
		for i in range(len(tup) - 1):
			current.append(tup[i])
			all.append(tuple(current))

		return all

	def remove_dummies(self):
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
			raise TypeError('need a str or a tuple for str_to_tuple')
	
	def bind(self, fnc, *keys):
		if len(keys) == 0: return
		keys = tuple(map(self.str_to_tuple, keys))
		cmd = Command(fnc, keys)
		cmd.commandlist = self
		self.commandlist.append(cmd)
		for key in keys:
			self.paths[key] = cmd
	
class Command():
	def __init__(self, fnc, keys):
		self.fnc = fnc
		self.keys = keys
		self.commandlist = None

#	def rebind(keys):
#		self.keys = keys
#		self.commandlist.rebuild_paths()

	def execute(self, fm):
		self.fnc(fm)

if __name__ == '__main__':
	cl = CommandList()
	cl.initialize_commands()

	print(cl.paths)
