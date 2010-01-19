from os.path import realpath, abspath, dirname, ismount

def mount_path(path):
	"""Get the mount root of a directory"""
	path = abspath(realpath(path))
	while path != '/':
		if ismount(path):
			return path
		path = dirname(path)
	return '/'
