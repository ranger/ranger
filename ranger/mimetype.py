types = {'not loaded': True}

def load():
	import sys, os, pickle
	types.clear()

	f = open(os.path.join(sys.path[0], 'data/mime.dat'), 'rb')
	types.update(pickle.load(f))
	f.close()

def get():
	if 'not loaded' in types:
		load()
	return types
