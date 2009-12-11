from ranger.ext.get_all_modules import get_all_modules
from os.path import expanduser, dirname, exists, join

__all__ = get_all_modules(dirname(__file__))

from ranger.colorschemes import *

confpath = expanduser('~/.ranger')
if exists(join(confpath, 'colorschemes')):
	initpy = join(confpath, 'colorschemes/__init__.py')
	if not exists(initpy):
		open(initpy, 'w').write("""from ranger.ext.get_all_modules import get_all_modules
from os.path import dirname

__all__ = get_all_modules(dirname(__file__))
""")

	try:
		import sys
		sys.path[0:0] = [confpath]
		from colorschemes import *
	except ImportError:
		pass

