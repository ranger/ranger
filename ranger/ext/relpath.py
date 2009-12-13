import os
import ranger

def relpath(*paths):
	"""returns the path relative to rangers library directory"""
	return os.path.join(ranger.RANGERDIR, *paths)

def relpath_conf(*paths):
	"""returns the path relative to rangers configuration directory"""
	return os.path.join(ranger.CONFDIR, *paths)

