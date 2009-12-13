class KeyBuffer(tuple):
	"""Extension of tuple suited to be used as a keybuffer"""
	def __str__(self):
		"""returns a concatenation of all characters"""
		return "".join( map( to_string, self ) )

def to_string(i):
	try:
		return chr(i)
	except ValueError:
		return '?'
