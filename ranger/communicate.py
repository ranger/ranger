import os

def _get_XDG_dir(varname, default_dirname):
	try:
		path = os.environ[varname]
	except:
		path = ''
	if path:
		result = os.sep.join([path, 'ranger'])
	else:
		result = os.sep.join([os.environ['HOME'], default_dirname, 'ranger'])
	try:
		os.makedirs(result)
	except:
		pass
	return result


def cache_dir():
	return _get_XDG_dir('XDG_CACHE_HOME', '.cache')


def conf_dir():
	return _get_XDG_dir('XDG_CONFIG_HOME', '.config')


def echo(text, filename):
	try:
		f = open(os.sep.join([cache_dir(), filename]), 'w')
	except:
		return False
	f.write(text)
	f.close()
