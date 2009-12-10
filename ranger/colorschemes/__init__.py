from ranger import get_all, log
from os.path import expanduser, dirname, exists, join

__all__ = get_all(dirname(__file__))

from ranger.colorschemes import *

confpath = expanduser('~/.ranger')
if exists(join(confpath, 'colorschemes')):
	initpy = join(confpath, 'colorschemes/__init__.py')
	if not exists(initpy):
		open(initpy, 'w').write("""import ranger, os.path
__all__ = ranger.get_all( os.path.dirname( __file__ ) )
""")

	try:
		import sys
		sys.path[0:0] = [confpath]
		from colorschemes import *
	except ImportError:
		pass

