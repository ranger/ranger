def relpath(*paths):
	"""returns the path relative to rangers library directory"""
	from os.path import join
	from ranger import RANGERDIR
	return join(RANGERDIR, *paths)
