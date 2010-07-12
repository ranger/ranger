rows = ([-1, 1],   # [level, ratio]
		[0,  3],
		[1,  4])

keys_raw = {
	'j': lambda s: s.move(min(s.cwd.pointer + 1, len(s.cwd.files) - 1)),
	'k': lambda s: s.move(max(s.cwd.pointer - 1, 0)),
	'h': lambda s: s.cd('..'),
	'l': lambda s: s.cd(s.cwd.current_file.basename),
	'G': lambda s: s.move(len(s.cwd.files) - 1),
	'g': lambda s: setattr(s, 'keymap', g_keys),
	'Q': lambda s: s.exit(),
}

g_keys_raw = {
	'g': lambda s: s.move(0),
	'h': lambda s: s.cd('~'),
	'/': lambda s: s.cd('/'),
	None: lambda s: None  # happens in any case. this breaks key chain
}

def leave_keychain(fnc):
	def new_fnc(status):
		status.keymap = keys
		return fnc(status)
	return new_fnc

def normalize_key(c):
	try:
		return ord(c)
	except:
		return c

g_keys = dict((normalize_key(c), leave_keychain(fnc)) \
		for c, fnc in g_keys_raw.items())
keys = dict((normalize_key(c), fnc) for c, fnc in keys_raw.items())
