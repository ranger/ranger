class KeyBuffer(tuple):
	def __str__(self):
		return "".join( map( to_string, self ) )

def to_string(i):
	try:
		return chr(i)
	except ValueError:
		return '?'
