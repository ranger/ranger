import os
import sys

confdir = os.path.expanduser('~/.ranger')
rangerdir = os.path.dirname(__file__)

sys.path.append(confdir)


def relpath(*args):
	return os.path.join(rangerdir, *args)

LOGFILE = '/tmp/errorlog'

def log(txt):
	f = open(LOGFILE, 'a')
	f.write("r1: ")
	f.write(str(txt))
	f.write("\n")
	f.close()

# used to get all colorschemes in ~/.ranger/colorschemes
# and ranger/colorschemes
def get_all(dirname):
	import os
	result = []
	for filename in os.listdir(dirname):
		if filename.endswith('.py') and not filename.startswith('_'):
			result.append(filename[0:filename.index('.')])
	return result
