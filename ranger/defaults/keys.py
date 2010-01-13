# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
Syntax for binding keys: bind(*keys, fnc)

keys are one or more key-combinations which are either:
* a string
* an integer which represents an ascii code
* a tuple of integers

fnc is a function which is called with the CommandArgument object.

The CommandArgument object has these methods:
cmdarg.fm: the file manager instance
cmdarg.wdg: the widget or ui instance
cmdarg.n: the number typed before the key combination (if allowed)
cmdarg.keys: the string representation of the used key combination
cmdarg.keybuffer: the keybuffer instance

Check ranger.keyapi for more information
"""

from ranger.keyapi import *

def system_functions(command_list):
	"""Each commandlist should have those."""
	bind, hint = make_abbreviations(command_list)

	bind(KEY_RESIZE, fm.resize())
	bind(KEY_MOUSE, fm.handle_mouse())
	bind('Q', fm.exit())
	bind(ctrl('L'), fm.redraw_window())

def initialize_commands(command_list):
	"""Initialize the commands for the main user interface"""

	bind, hint = make_abbreviations(command_list)

	# -------------------------------------------------------- movement
	bind('j', KEY_DOWN, fm.move_pointer(relative=1))
	bind('k', KEY_UP, fm.move_pointer(relative=-1))
	bind('l', KEY_RIGHT, fm.move_right())
	bind('h', KEY_LEFT, KEY_BACKSPACE, DEL, fm.move_left(1))

	bind(KEY_ENTER, ctrl('j'), fm.move_right(mode=1))

	bind('gg', KEY_HOME, fm.move_pointer(absolute=0))
	bind('G', KEY_END, fm.move_pointer(absolute=-1))
	bind('%', fm.move_pointer_by_percentage(absolute=50))
	bind(KEY_NPAGE, ctrl('f'), fm.move_pointer_by_pages(1))
	bind(KEY_PPAGE, ctrl('b'), fm.move_pointer_by_pages(-1))
	bind('J', ctrl('d'), fm.move_pointer_by_pages(0.5))
	bind('K', ctrl('u'), fm.move_pointer_by_pages(-0.5))

	bind('H', fm.history_go(-1))
	bind('L', fm.history_go(1))

	# ----------------------------------------------- tagging / marking
	bind('b', fm.tag_toggle())
	bind('B', fm.tag_remove())

	bind(' ', fm.mark(toggle=True))
	bind('v', fm.mark(all=True, toggle=True))
	bind('V', fm.mark(all=True, val=False))

	# ------------------------------------------ file system operations
	bind('yy', fm.copy())
	bind('dd', fm.cut())
	bind('pp', fm.paste())
	bind('pl', fm.paste_symlink())
	hint('p', 'press //p// once again to confirm pasting' \
			', or //l// to create symlinks')

	# ---------------------------------------------------- run programs
	bind('s', fm.execute_command('bash'))
	bind('E', fm.edit_file())
	bind('term', fm.execute_command('x-terminal-emulator', flags='d'))
	bind('du', fm.execute_command('du --max-depth=1 -h | less'))

	# -------------------------------------------------- toggle options
	hint('t', "show_//h//idden //p//review_files //d//irectories_first " \
			"//c//ollapse_preview")
	bind('th', fm.toggle_boolean_option('show_hidden'))
	bind('tp', fm.toggle_boolean_option('preview_files'))
	bind('td', fm.toggle_boolean_option('directories_first'))
	bind('tc', fm.toggle_boolean_option('collapse_preview'))

	# ------------------------------------------------------------ sort
	hint('o', 'O', "//s//ize //b//ase//n//ame //m//time //t//ype //r//everse")
	sort_dict = {
		's': 'size',
		'b': 'basename',
		'n': 'basename',
		'm': 'mtime',
		't': 'type',
	}

	for key, val in sort_dict.items():
		for key, is_capital in ((key, False), (key.upper(), True)):
			# reverse if any of the two letters is capital
			bind('o' + key, fm.sort(func=val, reverse=is_capital))
			bind('O' + key, fm.sort(func=val, reverse=True))

	bind('or', 'Or', 'oR', 'OR', lambda arg: \
			arg.fm.sort(reverse=not arg.fm.settings.reverse))

	# ----------------------------------------------- console shortcuts
	bind('A', lambda arg: arg.fm.open_console(cmode.COMMAND,
		'rename ' + arg.fm.env.cf.basename))
	bind('cw', fm.open_console(cmode.COMMAND, 'rename '))
	bind('cd', fm.open_console(cmode.COMMAND, 'cd '))
	bind('f', fm.open_console(cmode.COMMAND_QUICK, 'find '))
	bind('tf', fm.open_console(cmode.COMMAND, 'filter '))
	hint('d', 'd//u// (disk usage) d//d// (cut)')

	# --------------------------------------------- jump to directories
	bind('gh', fm.enter_dir('~'))
	bind('ge', fm.enter_dir('etc'))
	bind('gu', fm.enter_dir('/usr'))
	bind('gr', fm.enter_dir('/'))
	bind('gm', fm.enter_dir('/media'))
	bind('gn', fm.enter_dir('/mnt'))
	bind('gt', fm.enter_dir('~/.trash'))
	bind('gs', fm.enter_dir('/srv'))
	bind('gR', fm.enter_dir(RANGERDIR))

	# ------------------------------------------------------- searching
	bind('/', fm.open_console(cmode.SEARCH))

	bind('n', fm.search())
	bind('N', fm.search(forward=False))

	bind(TAB, fm.search(order='tag'))
	bind('cc', fm.search(order='ctime'))
	bind('cm', fm.search(order='mimetype'))
	bind('cs', fm.search(order='size'))
	hint('c', '//c//time //m//imetype //s//ize')

	# ------------------------------------------------------- bookmarks
	for key in ALLOWED_BOOKMARK_KEYS:
		bind("`" + key, "'" + key, fm.enter_bookmark(key))
		bind("m" + key, fm.set_bookmark(key))
		bind("um" + key, fm.unset_bookmark(key))

	# ---------------------------------------------------- change views
	bind('i', fm.display_file())
	bind(ctrl('p'), fm.display_log())
	bind('?', KEY_F1, fm.display_help())
	bind('w', lambda arg: arg.fm.ui.open_taskview())

	# ------------------------------------------------ system functions
	system_functions(command_list)
	bind('ZZ', fm.exit())
	bind(ctrl('R'), fm.reset())
	bind('R', fm.reload_cwd())
	bind(ctrl('C'), fm.exit())

	bind(':', ';', fm.open_console(cmode.COMMAND))
	bind('>', fm.open_console(cmode.COMMAND_QUICK))
	bind('!', fm.open_console(cmode.OPEN))
	bind('r', fm.open_console(cmode.OPEN_QUICK))

	command_list.rebuild_paths()


def initialize_console_commands(command_list):
	"""Initialize the commands for the console widget only"""

	bind, hint = make_abbreviations(command_list)

	# movement
	bind(KEY_UP, wdg.history_move(-1))
	bind(KEY_DOWN, wdg.history_move(1))
	bind(ctrl('b'), KEY_LEFT, wdg.move(relative = -1))
	bind(ctrl('f'), KEY_RIGHT, wdg.move(relative = 1))
	bind(ctrl('a'), KEY_HOME, wdg.move(absolute = 0))
	bind(ctrl('e'), KEY_END, wdg.move(absolute = -1))
	bind(ctrl('d'), KEY_DC, wdg.delete(0))
	bind(ctrl('h'), KEY_BACKSPACE, DEL, wdg.delete(-1))
	bind(ctrl('w'), wdg.delete_word())
	bind(ctrl('k'), wdg.delete_rest(1))
	bind(ctrl('u'), wdg.delete_rest(-1))
	bind(ctrl('y'), wdg.paste())
	bind(KEY_F1, lambda arg: arg.fm.display_command_help(arg.wdg))

	# system functions
	system_functions(command_list)
	bind(ctrl('c'), ESC, wdg.close())
	bind(ctrl('j'), KEY_ENTER, wdg.execute())
	bind(TAB, wdg.tab())
	bind(KEY_BTAB, wdg.tab(-1))

	# type keys
	def type_key(arg):
		arg.wdg.type_key(arg.keys)

	for i in range(ord(' '), ord('~')+1):
		bind(i, type_key)

	command_list.rebuild_paths()

def initialize_taskview_commands(command_list):
	"""Initialize the commands for the TaskView widget"""

	system_functions(command_list)
	bind, hint = make_abbreviations(command_list)

	bind('j', KEY_DOWN, wdg.move(relative=1))
	bind('k', KEY_UP, wdg.move(relative=-1))
	bind('gg', wdg.move(absolute=0))
	bind('G', wdg.move(absolute=-1))
	bind('K', wdg.task_move(0))
	bind('J', wdg.task_move(-1))

	bind('?', fm.display_help())

	bind('dd', wdg.task_remove())
	bind('w', 'q', ESC, ctrl('d'), ctrl('c'),
			lambda arg: arg.fm.ui.close_taskview())

	command_list.rebuild_paths()

def initialize_pager_commands(command_list):
	bind, hint = make_abbreviations(command_list)
	initialize_embedded_pager_commands(command_list)

	bind('q', 'i', ESC, KEY_F1, lambda arg: arg.fm.ui.close_pager())
	command_list.rebuild_paths()

def initialize_embedded_pager_commands(command_list):
	system_functions(command_list)
	bind, hint = make_abbreviations(command_list)

	bind('?', fm.display_help())

	bind('j', KEY_DOWN, wdg.move(relative=1))
	bind('k', KEY_UP, wdg.move(relative=-1))
	bind('gg', KEY_HOME, wdg.move(absolute=0))
	bind('G', KEY_END, wdg.move(absolute=-1))
	bind('J', ctrl('d'), wdg.move(relative=0.5, pages=True))
	bind('K', ctrl('u'), wdg.move(relative=-0.5, pages=True))
	bind(KEY_NPAGE, ctrl('f'), wdg.move(relative=1, pages=True))
	bind(KEY_PPAGE, ctrl('b'), wdg.move(relative=-1, pages=True))
	bind('E', fm.edit_file())

	bind('h', wdg.move_horizontal(relative=-4))
	bind('l', wdg.move_horizontal(relative=4))

	bind('q', 'i', ESC, lambda arg: arg.fm.ui.close_embedded_pager())
	command_list.rebuild_paths()
