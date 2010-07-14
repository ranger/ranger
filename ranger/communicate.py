import os

def cache_dir():
	try:
		path = os.environ['XDG_CACHE_HOME']
	except:
		path = ''
	if not path:
		return os.sep.join([os.environ['HOME'], '.cache', 'ranger'])
	return os.sep.join([path, 'ranger'])

def echo(text, filename):
	directory = cache_dir()
	try: os.makedirs(directory)
	except: pass
	try: f = open(os.sep.join([directory, filename]), 'w')
	except: return False
	f.write(text)
	f.close()
