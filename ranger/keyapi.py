from curses import *
from curses.ascii import *
from ranger import RANGERDIR
from ranger.gui.widgets import console_mode as cmode
from ranger.container.bookmarks import ALLOWED_KEYS as ALLOWED_BOOKMARK_KEYS

def make_abbreviations(command_list):
	def bind(*args):
		command_list.bind(args[-1], *args[:-1])
	
	def hint(*args):
		command_list.hint(args[-1], *args[:-1])

	return bind, hint

class Wrapper(object):
	def __init__(self, firstattr):
		self.__firstattr__ = firstattr

	def __getattr__(self, attr):
		def wrapper(*args, **keywords):
			def bla(command_argument):
				obj = getattr(command_argument, self.__firstattr__)
				if obj is None:
					return
				return getattr(obj, attr)(*args, **keywords)
			return bla
		return wrapper

fm = Wrapper('fm')
wdg = Wrapper('wdg')

# fm.enter_dir('~') is translated into lambda arg: arg.fm.enter_dir('~')
# this makes things like this possible:
# bind('gh', fm.enter_dir('~'))
#
# but NOT: (note the 2 dots)
# bind('H', fm.history.go(-1))
#
# for something like that, use the long version:
# bind('H', lambda arg: arg.fm.history.go(-1))


# Another wrapper for common actions which use a numerical argument:
class nwrap(object):
	@staticmethod
	def move(relative=0, absolute=None, pages=False):
		if absolute is None:
			def fnc(arg):
				if arg.n is not None:
					if relative >= 0:
						arg.wdg.move(relative=arg.n, pages=pages)
					else:
						arg.wdg.move(relative=-arg.n, pages=pages)
				else:
					arg.wdg.move(relative=relative, pages=pages)
		else:
			def fnc(arg):
				if arg.n is not None:
					arg.wdg.move(absolute=arg.n, relative=relative, pages=pages)
				else:
					arg.wdg.move(absolute=absolute, relative=relative, pages=pages)
		return fnc
