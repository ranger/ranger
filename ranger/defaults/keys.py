import curses
from curses import *
from curses.ascii import *
from ranger import RANGERDIR
from ranger import log
from ranger.gui.widgets.console import Console
from ranger.container.bookmarks import ALLOWED_KEYS as ALLOWED_BOOKMARK_KEYS

# syntax for binding keys: bind(*keys, fnc)
# fnc is a function which is called with the FM instance,
# keys are one or more key-combinations which are either:
# * a string
# * an integer which represents an ascii code
# * a tuple of integers
#
# in initialize_console_commands, fnc is a function which is
# called with the console widget instance instead.

def initialize_commands(command_list):
	"""Initialize the commands for the main user interface"""

	def do(method, *args, **kw):
		return lambda fm, n: getattr(fm, method)(*args, **kw)

	def bind(*args):
		command_list.bind(args[-1], *args[:-1])

	bind('l', KEY_RIGHT, do('move_right'))
	bind(KEY_ENTER, ctrl('j'), do('move_right', mode=1))
	bind('H', do('history_go', -1))
	bind('L', do('history_go',  1))
	bind('J', do('move_pointer_by_pages', 0.5))
	bind('K', do('move_pointer_by_pages', -0.5))
	bind('E', do('edit_file'))
#	bind('o', do('force_load_preview'))
	bind('i', do('tag_toggle'))
	bind('I', do('tag_remove'))

	bind(' ', do('mark', toggle=True))
	bind('v', do('mark', all=True, toggle=True))
	bind('V', do('mark', all=True, val=False))

	bind('yy', 'cp', do('copy'))
	bind('cut', do('cut'))
	bind('p', do('paste'))

	bind('s', do('spawn', 'bash'))

	t_hint = "show_//h//idden //p//review_files //d//irectories_first //a//uto_load_preview //c//ollapse_preview"
	command_list.hint(t_hint, 't')
	bind('th', do('toggle_boolean_option', 'show_hidden'))
	bind('tp', do('toggle_boolean_option', 'preview_files'))
	bind('td', do('toggle_boolean_option', 'directories_first'))
	bind('ta', do('toggle_boolean_option', 'auto_load_preview'))
	bind('tc', do('toggle_boolean_option', 'collapse_preview'))

	sort_hint = "//s//ize //b//ase//n//ame //m//time //t//ype //r//everse"
	sort_dict = {
		's': 'size',
		'b': 'basename',
		'n': 'basename',
		'm': 'mtime',
		't': 'type',
	}
	for key, val in sort_dict.items():
		for key, is_upper in ((key.lower(), False), (key.upper(), True)):
			# reverse if any of the two letters is capital
			bind('o' + key, do('sort', func=val, reverse=is_upper))
			bind('O' + key, do('sort', func=val, reverse=True))
	bind('or', 'Or', 'oR', 'OR', lambda fm, n: \
			fm.sort(reverse=not fm.settings.reverse))
	command_list.hint(sort_hint, 'o', 'O')

	bind('cd', do('open_console', ':', 'cd '))
	bind('f', do('open_console', '>', 'find '))

	# key combinations which change the current directory
	def cd(path):
		return lambda fm: fm.enter_dir(path)

	bind('gh', do('cd', '~'))
	bind('ge', do('cd', '/etc'))
	bind('gu', do('cd', '/usr'))
	bind('gr', do('cd', '/'))
	bind('gm', do('cd', '/media'))
	bind('gn', do('cd', '/mnt'))
	bind('gt', do('cd', '~/.trash'))
	bind('gs', do('cd', '/srv'))
	bind('gR', do('cd', RANGERDIR))

	bind('n', do('search_forward'))
	bind('N', do('search_backward'))

	# bookmarks
	for key in ALLOWED_BOOKMARK_KEYS:
		bind("`" + key, "'" + key, do('enter_bookmark', key))
		bind("m" + key, do('set_bookmark', key))
		bind("um" + key, do('unset_bookmark', key))

	# system functions
	bind(ctrl('D'), 'q', 'ZZ', do('exit'))
	bind(ctrl('R'), do('reset'))
	bind(ctrl('L'), do('redraw_window'))
	bind(ctrl('C'), do('interrupt'))
	bind(KEY_RESIZE, do('resize'))
	bind(KEY_MOUSE, do('handle_mouse'))
	bind(':', do('open_console', ':'))
	bind('>', do('open_console', '>'))
	bind('/', do('open_console', '/'))
	bind('?', do('open_console', '?'))
	bind('!', do('open_console', '!'))
	bind('r', do('open_console', '@'))


	# definitions which require their own function:
	def test(fm, n):
		from ranger import log
		log(fm.bookmarks.dct)
	bind('x', test)

	def ggG(default):
		# moves to an absolute point, or to a predefined default
		# if no number is specified.
		return lambda fm, n: \
				fm.move_pointer(absolute=(n or default)-1)

	bind('gg', ggG(1))
	bind('G', ggG(0))

	bind('%', lambda fm, n: fm.move_pointer_by_percentage(absolute=n or 50))

	def jk(direction):
		# moves up or down by the specified number or one, in
		# the predefined direction
		return lambda fm, n: \
				fm.move_pointer(relative=(n or 1) * direction)

	bind('j', KEY_DOWN, jk(1))
	bind('k', KEY_UP, jk(-1))

	bind('h', KEY_LEFT, KEY_BACKSPACE, DEL, lambda fm, n: \
			fm.move_left(n or 1))

	bind('w', lambda fm, n: fm.ui.open_pman())

	command_list.rebuild_paths()


def initialize_console_commands(command_list):
	"""Initialize the commands for the console widget only"""

	def bind(*args):
		command_list.bind(args[-1], *args[:-1])

	def do(method, *args, **kw):
		return lambda widget: getattr(widget, method)(*args, **kw)

	def do_fm(method, *args, **kw):
		return lambda widget: getattr(widget.fm, method)(*args, **kw)

	# movement
	bind(KEY_UP, do('history_move', -1))
	bind(KEY_DOWN, do('history_move', 1))
	bind(ctrl('b'), KEY_LEFT, do('move', relative = -1))
	bind(ctrl('f'), KEY_RIGHT, do('move', relative = 1))
	bind(ctrl('a'), KEY_HOME, do('move', absolute = 0))
	bind(ctrl('e'), KEY_END, do('move', absolute = -1))
	bind(ctrl('d'), KEY_DC, do('delete', 0))
	bind(ctrl('h'), KEY_BACKSPACE, DEL, do('delete', -1))
	bind(ctrl('w'), do('delete_word'))
	bind(ctrl('k'), do('delete_rest', 1))
	bind(ctrl('u'), do('delete_rest', -1))
	bind(ctrl('y'), do('paste'))

	# system functions
	bind(ctrl('c'), ESC, do('close'))
	bind(ctrl('j'), KEY_ENTER, do('execute'))
	bind(ctrl('l'), do_fm('redraw'))
	bind(TAB, do('tab'))
	bind(KEY_BTAB, do('tab', -1))
	bind(KEY_RESIZE, do_fm('resize'))

	# type keys
	def type_key(key):
		return lambda con: con.type_key(key)

	for i in range(ord(' '), ord('~')+1):
		bind(i, type_key(i))

	command_list.rebuild_paths()

def initialize_process_manager_commands(command_list):
	"""Initialize the commands for the process manager widget"""

	from ranger.gui.widgets.process_manager import KeyWrapper as wdg

	def bind(*args):
		command_list.bind(args[-1], *args[:-1])

	def do(method, *args, **kw):
		return lambda widget, n: getattr(widget, method)(*args, **kw)

	def do_fm(method, *args, **kw):
		return lambda widget, n: getattr(widget.fm, method)(*args, **kw)

	bind('j', KEY_DOWN, wdg.move(relative=1))
	bind('k', KEY_UP, wdg.move(relative=-1))
	bind('gg', wdg.move(absolute=0))
	bind('G', wdg.move(absolute=-1))
	bind('K', lambda wdg, n: wdg.process_move(0))
	bind('J', lambda wdg, n: wdg.process_move(-1))

	bind('dd', do('process_remove'))
	bind('w', ESC, ctrl('d'), ctrl('c'),
			lambda wdg, n: wdg.fm.ui.close_pman())
	bind(KEY_RESIZE, do_fm('resize'))

	command_list.rebuild_paths()
