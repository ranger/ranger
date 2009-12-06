
import sys, os
sys.path[0:0] = [os.path.expanduser('~/.ranger')]

try:
	import keys
except ImportError:
	from ranger.defaults import keys

try:
	import apps
except ImportError:
	from ranger.defaults import apps

try:
	import options
except ImportError:
	from ranger.defaults import options
