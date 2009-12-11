def get_all_modules(dirname):
	"""returns a list of strings containing the names of modules in a directory"""
	import os
	result = []
	for filename in os.listdir(dirname):
		if filename.endswith('.py') and not filename.startswith('_'):
			result.append(filename[0:filename.index('.')])
	return result
