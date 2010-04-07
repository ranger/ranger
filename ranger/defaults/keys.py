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
Syntax for binding keys: map(*keys, fnc)

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

# NOTE: The "map" object used below is a callable CommandList
# object and NOT the builtin python map function!

from ranger.api.keys import *

def _vimlike_aliases(map):
	alias = map.alias

	# the key 'k' will always do the same as KEY_UP, etc.
	alias(KEY_UP, 'k')
	alias(KEY_DOWN, 'j')
	alias(KEY_LEFT, 'h')
	alias(KEY_RIGHT, 'l')

	alias(KEY_NPAGE, ctrl('f'))
	alias(KEY_PPAGE, ctrl('b'))
	alias(KEY_HOME, 'gg')
	alias(KEY_END, 'G')


def _emacs_aliases(map):
	alias = map.alias
	alias(KEY_LEFT, ctrl('b'))
	alias(KEY_RIGHT, ctrl('f'))
	alias(KEY_HOME, ctrl('a'))
	alias(KEY_END, ctrl('e'))
	alias(KEY_DC, ctrl('d'))
	alias(DEL, ctrl('h'))


def initialize_commands(map):
	"""Initialize the commands for the main user interface"""

	# -------------------------------------------------------- movement
	_vimlike_aliases(map)
	_basic_movement(map)

	map.alias(KEY_LEFT, KEY_BACKSPACE, DEL)
	map.alias(KEY_RIGHT, KEY_ENTER, ctrl('j'))

	map('%', fm.move(to=50, percentage=True))
	map(KEY_NPAGE, ctrl('f'), fm.move(down=1, pages=True))
	map(KEY_PPAGE, ctrl('b'), fm.move(up=1, pages=True))
	map(ctrl('d'), 'J', fm.move(down=0.5, pages=True))
	map(ctrl('u'), 'K', fm.move(up=0.5, pages=True))

	map(']', fm.traverse())
	map('[', fm.history_go(-1))

	# --------------------------------------------------------- history
	map('H', fm.history_go(-1))
	map('L', fm.history_go(1))

	# ----------------------------------------------- tagging / marking
	map('t', fm.tag_toggle())
	map('T', fm.tag_remove())

	map(' ', fm.mark(toggle=True))
	map('v', fm.mark(all=True, toggle=True))
	map('V', fm.mark(all=True, val=False))

	# ------------------------------------------ file system operations
	map('yy', fm.copy())
	map('dd', fm.cut())
	map('pp', fm.paste())
	map('po', fm.paste(overwrite=True))
	map('pl', fm.paste_symlink())
	map('p', hint='press //p// once again to confirm pasting' \
			', or //l// to create symlinks')

	# ---------------------------------------------------- run programs
	map('s', fm.execute_command(os.environ['SHELL']))
	map('E', fm.edit_file())
	map(',term', fm.execute_command('x-terminal-emulator', flags='d'))
	map('du', fm.execute_command('du --max-depth=1 -h | less'))

	# -------------------------------------------------- toggle options
	map('b', fm.notify('Warning: settings are now changed with z!', bad=True))
	map('z', hint="show_//h//idden //p//review_files //d//irectories_first " \
		"//c//ollapse_preview flush//i//nput ca//s//e_insensitive")
	map('zh', fm.toggle_boolean_option('show_hidden'))
	map('zp', fm.toggle_boolean_option('preview_files'))
	map('zP', fm.toggle_boolean_option('preview_directories'))
	map('zi', fm.toggle_boolean_option('flushinput'))
	map('zd', fm.toggle_boolean_option('sort_directories_first'))
	map('zc', fm.toggle_boolean_option('collapse_preview'))
	map('zs', fm.toggle_boolean_option('sort_case_insensitive'))

	# ------------------------------------------------------------ sort
	map('o', 'O', hint="//s//ize //b//ase//n//ame //m//time //t//ype //r//everse")
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
			map('o' + key, fm.sort(func=val, reverse=is_capital))
			map('O' + key, fm.sort(func=val, reverse=True))

	map('or', 'Or', 'oR', 'OR', lambda arg: \
			arg.fm.sort(reverse=not arg.fm.settings.sort_reverse))

	# ----------------------------------------------- console shortcuts
	@map("A")
	def append_to_filename(arg):
		command = 'rename ' + arg.fm.env.cf.basename
		arg.fm.open_console(cmode.COMMAND, command)

	map('cw', fm.open_console(cmode.COMMAND, 'rename '))
	map('cd', fm.open_console(cmode.COMMAND, 'cd '))
	map('f', fm.open_console(cmode.COMMAND_QUICK, 'find '))
	map('tf', fm.open_console(cmode.COMMAND, 'filter '))
	map('d', hint='d//u// (disk usage) d//d// (cut)')
	map('@', fm.open_console(cmode.OPEN, '@'))
	map('#', fm.open_console(cmode.OPEN, 'p!'))

	# --------------------------------------------- jump to directories
	map('gh', fm.cd('~'))
	map('ge', fm.cd('/etc'))
	map('gu', fm.cd('/usr'))
	map('gd', fm.cd('/dev'))
	map('gl', fm.cd('/lib'))
	map('go', fm.cd('/opt'))
	map('gv', fm.cd('/var'))
	map('gr', 'g/', fm.cd('/'))
	map('gm', fm.cd('/media'))
	map('gn', fm.cd('/mnt'))
	map('gt', fm.cd('/tmp'))
	map('gs', fm.cd('/srv'))
	map('gR', fm.cd(RANGERDIR))

	# ------------------------------------------------------------ tabs
	map('gc', ctrl('W'), fm.tab_close())
	map('gt', TAB, fm.tab_move(1))
	map('gT', KEY_BTAB, fm.tab_move(-1))
	map('gn', ctrl('N'), fm.tab_new())
	for n in range(10):
		map('g' + str(n), fm.tab_open(n))

	# ------------------------------------------------------- searching
	map('/', fm.open_console(cmode.SEARCH))

	map('n', fm.search())
	map('N', fm.search(forward=False))

	map('ct', fm.search(order='tag'))
	map('cc', fm.search(order='ctime'))
	map('cm', fm.search(order='mimetype'))
	map('cs', fm.search(order='size'))
	map('c', hint='//c//time //m//imetype //s//ize //t//agged')

	# ------------------------------------------------------- bookmarks
	for key in ALLOWED_BOOKMARK_KEYS:
		map("`" + key, "'" + key, fm.enter_bookmark(key))
		map("m" + key, fm.set_bookmark(key))
		map("um" + key, fm.unset_bookmark(key))
	map("`", "'", "m", "um", draw_bookmarks=True)

	# ---------------------------------------------------- change views
	map('i', fm.display_file())
	map(ctrl('p'), fm.display_log())
	map('?', KEY_F1, fm.display_help())
	map('w', lambda arg: arg.fm.ui.open_taskview())

	# ------------------------------------------------ system functions
	_system_functions(map)
	map('ZZ', 'ZQ', fm.exit())
	map(ctrl('R'), fm.reset())
	map('R', fm.reload_cwd())
	@map(ctrl('C'))
	def ctrl_c(arg):
		try:
			item = arg.fm.loader.queue[0]
		except:
			arg.fm.notify("Type Q or :quit<Enter> to exit Ranger")
		else:
			arg.fm.notify("Aborting: " + item.get_description())
			arg.fm.loader.remove(index=0)

	map(':', ';', fm.open_console(cmode.COMMAND))
	map('>', fm.open_console(cmode.COMMAND_QUICK))
	map('!', fm.open_console(cmode.OPEN))
	map('r', fm.open_console(cmode.OPEN_QUICK))

	map.rebuild_paths()


def initialize_console_commands(map):
	"""Initialize the commands for the console widget only"""

	_basic_movement(map)
	_emacs_aliases(map)

	# -------------------------------------------------------- movement
	map(KEY_UP, wdg.history_move(-1))
	map(KEY_DOWN, wdg.history_move(1))
	map(KEY_HOME, wdg.move(right=0, absolute=True))
	map(KEY_END, wdg.move(right=-1, absolute=True))

	# ----------------------------------------- deleting / pasting text
	map(KEY_DC, wdg.delete(0))
	map(KEY_BACKSPACE, DEL, wdg.delete(-1))
	map(ctrl('w'), wdg.delete_word())
	map(ctrl('k'), wdg.delete_rest(1))
	map(ctrl('u'), wdg.delete_rest(-1))
	map(ctrl('y'), wdg.paste())

	# ------------------------------------------------ system functions
	map(KEY_F1, lambda arg: arg.fm.display_command_help(arg.wdg))
	map(ctrl('c'), ESC, wdg.close())
	map(ctrl('j'), KEY_ENTER, wdg.execute())
	map(TAB, wdg.tab())
	map(KEY_BTAB, wdg.tab(-1))

	map.rebuild_paths()


def initialize_taskview_commands(map):
	"""Initialize the commands for the TaskView widget"""
	_basic_movement(map)
	_vimlike_aliases(map)
	_system_functions(map)

	# -------------------------------------------------- (re)move tasks
	map('K', wdg.task_move(0))
	map('J', wdg.task_move(-1))
	map('dd', wdg.task_remove())

	# ------------------------------------------------ system functions
	map('?', fm.display_help())
	map('w', 'q', ESC, ctrl('d'), ctrl('c'),
			lambda arg: arg.fm.ui.close_taskview())

	map.rebuild_paths()


def initialize_pager_commands(map):
	_base_pager_commands(map)
	map('q', 'i', ESC, KEY_F1, lambda arg: arg.fm.ui.close_pager())
	map.rebuild_paths()


def initialize_embedded_pager_commands(map):
	_base_pager_commands(map)
	map('q', 'i', ESC, lambda arg: arg.fm.ui.close_embedded_pager())
	map.rebuild_paths()


def _base_pager_commands(map):
	_basic_movement(map)
	_vimlike_aliases(map)
	_system_functions(map)

	# -------------------------------------------------------- movement
	map(KEY_LEFT, wdg.move(left=4))
	map(KEY_RIGHT, wdg.move(right=4))
	map(KEY_NPAGE, ctrl('f'), wdg.move(down=1, pages=True))
	map(KEY_PPAGE, ctrl('b'), wdg.move(up=1, pages=True))
	map(ctrl('d'), wdg.move(down=0.5, pages=True))
	map(ctrl('u'), wdg.move(up=0.5, pages=True))
	map(' ', wdg.move(down=0.8, pages=True))

	# ---------------------------------------------------------- others
	map('E', fm.edit_file())
	map('?', fm.display_help())

	# --------------------------------------------- less-like shortcuts
	map.alias(KEY_NPAGE, 'f')
	map.alias(KEY_PPAGE, 'b')
	map.alias(ctrl('d'), 'd')
	map.alias(ctrl('u'), 'u')


def _system_functions(map):
	map('Q', fm.exit())
	map(ctrl('L'), fm.redraw_window())


def _basic_movement(map):
	map(KEY_DOWN, wdg.move(down=1))
	map(KEY_UP, wdg.move(up=1))
	map(KEY_RIGHT, wdg.move(right=1))
	map(KEY_LEFT, wdg.move(left=1))
	map(KEY_HOME, wdg.move(to=0))
	map(KEY_END, wdg.move(to=-1))
