# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This is the default key configuration file of ranger.
Syntax for binding keys: bind(*keys, fnc)

keys are one or more key-combinations which are either:
* a string
* an integer which represents an ascii code
* a tuple of integers

fnc is a function which is called with the CommandArgument object.

The CommandArgument object has these attributes:
arg.fm: the file manager instance
arg.wdg: the widget or ui instance
arg.n: the number typed before the key combination (if allowed)
arg.keys: the string representation of the used key combination
arg.keybuffer: the keybuffer instance

Check ranger.keyapi for more information
"""

from ranger.api.keys import *

def _vimlike_aliases(command_list):
	bind, alias = make_abbreviations(command_list)

	# the key 'k' will always do the same as KEY_UP, etc.
	alias(KEY_UP, 'k')
	alias(KEY_DOWN, 'j')
	alias(KEY_LEFT, 'h')
	alias(KEY_RIGHT, 'l')

	alias(KEY_NPAGE, ctrl('f'))
	alias(KEY_PPAGE, ctrl('b'))
	alias(KEY_HOME, 'gg')
	alias(KEY_END, 'G')

	# I like to move quickly with J/K
	alias(ctrl('d'), 'J')
	alias(ctrl('u'), 'K')

def initialize_commands(command_list):
	"""Initialize the commands for the main user interface"""

	bind, alias = make_abbreviations(command_list)

	# -------------------------------------------------------- movement
	_vimlike_aliases(command_list)
	command_list.alias(KEY_LEFT, KEY_BACKSPACE, DEL)

	bind(KEY_DOWN, fm.move_pointer(relative=1))
	bind(KEY_UP, fm.move_pointer(relative=-1))
	bind(KEY_RIGHT, KEY_ENTER, ctrl('j'), fm.move_right())
	bind(KEY_LEFT, KEY_BACKSPACE, DEL, fm.move_left(1))
	bind(KEY_HOME, fm.move_pointer(absolute=0))
	bind(KEY_END, fm.move_pointer(absolute=-1))

	bind(KEY_HOME, fm.move_pointer(absolute=0))
	bind(KEY_END, fm.move_pointer(absolute=-1))

	bind('%', fm.move_pointer_by_percentage(absolute=50))
	bind(KEY_NPAGE, fm.move_pointer_by_pages(1))
	bind(KEY_PPAGE, fm.move_pointer_by_pages(-1))
	bind(ctrl('d'), fm.move_pointer_by_pages(0.5))
	bind(ctrl('u'), fm.move_pointer_by_pages(-0.5))

	bind(']', fm.traverse())
	bind('[', fm.history_go(-1))

	# --------------------------------------------------------- history
	bind('H', fm.history_go(-1))
	bind('L', fm.history_go(1))

	# ----------------------------------------------- tagging / marking
	bind('t', fm.tag_toggle())
	bind('T', fm.tag_remove())

	bind(' ', fm.mark(toggle=True))
	bind('v', fm.mark(all=True, toggle=True))
	bind('V', fm.mark(all=True, val=False))

	# ------------------------------------------ file system operations
	bind('yy', fm.copy())
	bind('dd', fm.cut())
	bind('pp', fm.paste())
	bind('po', fm.paste(overwrite=True))
	bind('pl', fm.paste_symlink())
	bind('p', hint='press //p// once again to confirm pasting' \
			', or //l// to create symlinks')

	# ---------------------------------------------------- run programs
	bind('s', fm.execute_command(os.environ['SHELL']))
	bind('E', fm.edit_file())
	bind(',term', fm.execute_command('x-terminal-emulator', flags='d'))
	bind('du', fm.execute_command('du --max-depth=1 -h | less'))

	# -------------------------------------------------- toggle options
	bind('b', hint="bind_//h//idden //p//review_files //d//irectories_first " \
			"//c//ollapse_preview flush//i//nput")
	bind('bh', fm.toggle_boolean_option('show_hidden'))
	bind('bp', fm.toggle_boolean_option('preview_files'))
	bind('bi', fm.toggle_boolean_option('flushinput'))
	bind('bd', fm.toggle_boolean_option('directories_first'))
	bind('bc', fm.toggle_boolean_option('collapse_preview'))

	# ------------------------------------------------------------ sort
	bind('o', 'O', hint="//s//ize //b//ase//n//ame //m//time //t//ype //r//everse")
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
	@bind("A")
	def append_to_filename(arg):
		command = 'rename ' + arg.fm.env.cf.basename
		arg.fm.open_console(cmode.COMMAND, command)

	bind('cw', fm.open_console(cmode.COMMAND, 'rename '))
	bind('cd', fm.open_console(cmode.COMMAND, 'cd '))
	bind('f', fm.open_console(cmode.COMMAND_QUICK, 'find '))
	bind('tf', fm.open_console(cmode.COMMAND, 'filter '))
	bind('d', hint='d//u// (disk usage) d//d// (cut)')

	# --------------------------------------------- jump to directories
	bind('gh', fm.cd('~'))
	bind('ge', fm.cd('/etc'))
	bind('gu', fm.cd('/usr'))
	bind('gd', fm.cd('/dev'))
	bind('gl', fm.cd('/lib'))
	bind('go', fm.cd('/opt'))
	bind('gv', fm.cd('/var'))
	bind('gr', 'g/', fm.cd('/'))
	bind('gm', fm.cd('/media'))
	bind('gn', fm.cd('/mnt'))
	bind('gt', fm.cd('/tmp'))
	bind('gs', fm.cd('/srv'))
	bind('gR', fm.cd(RANGERDIR))

	# ------------------------------------------------------- searching
	bind('/', fm.open_console(cmode.SEARCH))

	bind('n', fm.search())
	bind('N', fm.search(forward=False))

	bind(TAB, fm.search(order='tag'))
	bind('cc', fm.search(order='ctime'))
	bind('cm', fm.search(order='mimetype'))
	bind('cs', fm.search(order='size'))
	bind('c', hint='//c//time //m//imetype //s//ize')

	# ------------------------------------------------------- bookmarks
	for key in ALLOWED_BOOKMARK_KEYS:
		bind("`" + key, "'" + key, fm.enter_bookmark(key))
		bind("m" + key, fm.set_bookmark(key))
		bind("um" + key, fm.unset_bookmark(key))
	bind("`", "'", "m", draw_bookmarks=True)

	# ---------------------------------------------------- change views
	bind('i', fm.display_file())
	bind(ctrl('p'), fm.display_log())
	bind('?', KEY_F1, fm.display_help())
	bind('w', lambda arg: arg.fm.ui.open_taskview())

	# ---------------------------------------------------------- custom
	# This is useful to track watched episode of a series.
	@bind(']')
	def tag_next_and_run(arg):
		fm = arg.fm
		fm.tag_remove()
		fm.tag_remove(movedown=False)
		fm.tag_toggle()
		fm.move_pointer(relative=-2)
		fm.move_right()
		fm.move_pointer(relative=1)

	# "enter" = shortcut for "1l"
	bind(KEY_ENTER, ctrl('j'), fm.move_right(mode=1))

	# ------------------------------------------------ system functions
	_system_functions(command_list)
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
	bind, alias = make_abbreviations(command_list)

	# -------------------------------------------------------- movement
	bind(KEY_UP, wdg.history_move(-1))
	bind(KEY_DOWN, wdg.history_move(1))

	bind(ctrl('b'), KEY_LEFT, wdg.move(relative = -1))
	bind(ctrl('f'), KEY_RIGHT, wdg.move(relative = 1))
	bind(ctrl('a'), KEY_HOME, wdg.move(absolute = 0))
	bind(ctrl('e'), KEY_END, wdg.move(absolute = -1))

	# ----------------------------------------- deleting / pasting text
	bind(ctrl('d'), KEY_DC, wdg.delete(0))
	bind(ctrl('h'), KEY_BACKSPACE, DEL, wdg.delete(-1))
	bind(ctrl('w'), wdg.delete_word())
	bind(ctrl('k'), wdg.delete_rest(1))
	bind(ctrl('u'), wdg.delete_rest(-1))
	bind(ctrl('y'), wdg.paste())

	# ----------------------------------------------------- typing keys
	def type_key(arg):
		arg.wdg.type_key(arg.keys)

	for i in range(ord(' '), ord('~')+1):
		bind(i, type_key)

	# ------------------------------------------------ system functions
	_system_functions(command_list)

	bind(KEY_F1, lambda arg: arg.fm.display_command_help(arg.wdg))
	bind(ctrl('c'), ESC, wdg.close())
	bind(ctrl('j'), KEY_ENTER, wdg.execute())
	bind(TAB, wdg.tab())
	bind(KEY_BTAB, wdg.tab(-1))

	command_list.rebuild_paths()


def initialize_taskview_commands(command_list):
	"""Initialize the commands for the TaskView widget"""
	bind, alias = make_abbreviations(command_list)
	_basic_movement(command_list)
	_vimlike_aliases(command_list)
	_system_functions(command_list)

	# -------------------------------------------------- (re)move tasks
	bind('K', wdg.task_move(0))
	bind('J', wdg.task_move(-1))
	bind('dd', wdg.task_remove())

	# ------------------------------------------------ system functions
	bind('?', fm.display_help())
	bind('w', 'q', ESC, ctrl('d'), ctrl('c'),
			lambda arg: arg.fm.ui.close_taskview())

	command_list.rebuild_paths()


def initialize_pager_commands(command_list):
	bind, alias = make_abbreviations(command_list)
	_base_pager_commands(command_list)
	bind('q', 'i', ESC, KEY_F1, lambda arg: arg.fm.ui.close_pager())
	command_list.rebuild_paths()


def initialize_embedded_pager_commands(command_list):
	bind, alias = make_abbreviations(command_list)
	_base_pager_commands(command_list)
	bind('q', 'i', ESC, lambda arg: arg.fm.ui.close_embedded_pager())
	command_list.rebuild_paths()


def _base_pager_commands(command_list):
	bind, alias = make_abbreviations(command_list)
	_basic_movement(command_list)
	_vimlike_aliases(command_list)
	_system_functions(command_list)

	# -------------------------------------------------------- movement
	bind(KEY_LEFT, wdg.move_horizontal(relative=-4))
	bind(KEY_RIGHT, wdg.move_horizontal(relative=4))
	bind(KEY_NPAGE, wdg.move(relative=1, pages=True))
	bind(KEY_PPAGE, wdg.move(relative=-1, pages=True))
	bind(ctrl('d'), wdg.move(relative=0.5, pages=True))
	bind(ctrl('u'), wdg.move(relative=-0.5, pages=True))

	# ---------------------------------------------------------- others
	bind('E', fm.edit_file())
	bind('?', fm.display_help())

	# --------------------------------------------- less-like shortcuts
	alias(KEY_NPAGE, 'd')
	alias(KEY_PPAGE, 'u')


def _system_functions(command_list):
	# Each commandlist should have this bindings
	bind, alias = make_abbreviations(command_list)

	bind(KEY_RESIZE, fm.resize())
	bind(KEY_MOUSE, fm.handle_mouse())
	bind('Q', fm.exit())
	bind(ctrl('L'), fm.redraw_window())


def _basic_movement(command_list):
	bind, alias = make_abbreviations(command_list)

	bind(KEY_DOWN, wdg.move(relative=1))
	bind(KEY_UP, wdg.move(relative=-1))
	bind(KEY_HOME, wdg.move(absolute=0))
	bind(KEY_END, wdg.move(absolute=-1))

def get_directions():
	k = KeyMap()
	map = k.add

	map('<down>', dir=Direction(down=1))
	map('<up>', dir=Direction(down=-1))
	map('<left>', dir=Direction(right=-1))
	map('<right>', dir=Direction(right=1))

	map('j', alias='<down>')
	map('k', alias='<up>')
	map('h', alias='<left>')
	map('l', alias='<right>')
	return k

def move(arg):
	arg.fm.move_pointer(relative=arg.direction.down)

def get_ui_keys():
	k = KeyMap()
	k.merge(system_keys())
	map = k.add

	map('<dir>', func=move)
	map('<C-c>', 'Q', func=fm.exit())

	# --------------------------------------------------------- history
	map('H', func=fm.history_go(-1))
	map('L', func=fm.history_go(1))

	# ----------------------------------------------- tagging / marking
	map('t', func=fm.tag_toggle())
	map('T', func=fm.tag_remove())

	map(' ', func=fm.mark(toggle=True))
	map('v', func=fm.mark(all=True, toggle=True))
	map('V', func=fm.mark(all=True, val=False))

	# ------------------------------------------ file system operations
	map('yy', func=fm.copy())
	map('dd', func=fm.cut())
	map('pp', func=fm.paste())
	map('po', func=fm.paste(overwrite=True))
	map('pl', func=fm.paste_symlink())
	map('p', hint='press //p// once again to confirm pasting' \
			', func=or //l// to create symlinks')

	# ---------------------------------------------------- run programs
	map('s', func=fm.execute_command(os.environ['SHELL']))
	map('E', func=fm.edit_file())
	map('term', func=fm.execute_command('x-terminal-emulator', flags='d'))
	map('du', func=fm.execute_command('du --max-depth=1 -h | less'))

	return k

def system_keys():
	k = KeyMap()
	k.map(fm.exit(), 'Q')
	k.map(fm.handle_mouse(), '<mouse>')
	k.map(fm.redraw_window(), '<C-L>')
	k.map(fm.resize(), '<resize>')
	return k


ui_keys = get_ui_keys()
taskview_keys = ui_keys
pager_keys = ui_keys
embedded_pager_keys = ui_keys
console_keys = ui_keys
directions = get_directions()
