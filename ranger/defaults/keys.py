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

Examples for keys: "x", "gg", "<C-J><A-4>", "<tab>", "<down><up><right>"

fnc is a function which is called with the CommandArgs object.

The CommandArgs object has these attributes:
arg.fm: the file manager instance
arg.wdg: the widget or ui instance
arg.n: the number typed before the key combination (if allowed)
arg.keys: the string representation of the used key combination
arg.keybuffer: the keybuffer instance
"""

from ranger.api.keys import *
from ranger import log

# ===================================================================
# == Define keys for everywhere:
# ===================================================================
map = global_keys = KeyMap()
map('Q', fm.exit())
map('<C-L>', fm.redraw_window())
map('<backspace2>', alias='<backspace>')  # Backspace is bugged sometimes

@map('<dir>') # move around with direction keys
def move(arg):
	arg.wdg.move(narg=arg.n, **arg.direction)

# ===================================================================
# == Define aliases
# ===================================================================
map = vim_aliases = KeyMap()
map('j', alias='<down>')
map('k', alias='<up>')
map('h', alias='<left>')
map('l', alias='<right>')
map('gg', alias='<home>')
map('G', alias='<end>')
map('<C-F>', alias='<pagedown>')
map('<C-B>', alias='<pageup>')

map = readline_aliases = KeyMap()
map('<C-B>', alias='<left>')
map('<C-F>', alias='<right>')
map('<C-A>', alias='<home>')
map('<C-E>', alias='<end>')
map('<C-D>', alias='<delete>')
map('<C-H>', alias='<backspace>')

# ===================================================================
# == Define keys in "general" context:
# ===================================================================
map = keymanager['general']
map.merge(global_keys)
map.merge(vim_aliases)

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
map('p<bg>', fm.hint('press //p// once again to confirm pasting' \
		', or //l// to create symlinks'))

# ---------------------------------------------------- run programs
map('s', fm.execute_command(os.environ['SHELL']))
map('E', fm.edit_file())
map('.term', fm.execute_command('x-terminal-emulator', flags='d'))
map('du', fm.execute_command('du --max-depth=1 -h | less'))

# -------------------------------------------------- toggle options
map('z<bg>', fm.hint("bind_//h//idden //p//review_files" \
	"//d//irectories_first //c//ollapse_preview flush//i//nput"))
map('zh', fm.toggle_boolean_option('show_hidden'))
map('zp', fm.toggle_boolean_option('preview_files'))
map('zi', fm.toggle_boolean_option('flushinput'))
map('zd', fm.toggle_boolean_option('directories_first'))
map('zc', fm.toggle_boolean_option('collapse_preview'))

# ------------------------------------------------------------ sort
map('o<bg>', 'O<bg>', fm.hint("//s//ize //b//ase//n//ame //m//time" \
	" //t//ype //r//everse"))
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
map('bf', fm.open_console(cmode.COMMAND, 'filter '))
map('d<bg>', fm.hint('d//u// (disk usage) d//d// (cut)'))
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
map('gs', fm.cd('/srv'))
map('gR', fm.cd(RANGERDIR))

# ------------------------------------------------------------ tabs
map('gc', '<C-W>', fm.tab_close())
map('gt', '<TAB>', fm.tab_move(1))
map('gT', '<S-TAB>', fm.tab_move(-1))
map('gn', '<C-N>', fm.tab_new())
for n in range(10):
	map('g' + str(n), fm.tab_open(n))
	map('<A-' + str(n) + '>', fm.tab_open(n))

# ------------------------------------------------------- searching
map('/', fm.open_console(cmode.SEARCH))

map('n', fm.search())
map('N', fm.search(forward=False))

map('ct', fm.search(order='tag'))
map('cc', fm.search(order='ctime'))
map('cm', fm.search(order='mimetype'))
map('cs', fm.search(order='size'))
map('c<bg>', fm.hint('//c//time //m//imetype //s//ize'))

# ------------------------------------------------------- bookmarks
for key in ALLOWED_BOOKMARK_KEYS:
	map("`" + key, "'" + key, fm.enter_bookmark(key))
	map("m" + key, fm.set_bookmark(key))
	map("um" + key, fm.unset_bookmark(key))
map("`<bg>", "'<bg>", "m<bg>", fm.draw_bookmarks())

# ---------------------------------------------------- change views
map('i', fm.display_file())
map('<C-P>', fm.display_log())
map('?', KEY_F1, fm.display_help())
map('w', lambda arg: arg.fm.ui.open_taskview())

# ------------------------------------------------ system functions
map('ZZ', fm.exit())
map('<C-R>', fm.reset())
map('R', fm.reload_cwd())
@map('<C-C>')
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

# ===================================================================
# == Define keys for the console
# ===================================================================
map = keymanager.get_context('console')
map.merge(global_keys)
map.merge(readline_aliases)
map.unmap('Q')  # don't quit with Q in console, so we can type it
map.unmap('<dir>')  # define my own direction keys

map('a', wdg.type_key('a'))
map('<up>', wdg.history_move(-1))
map('<down>', wdg.history_move(1))
map('<home>', wdg.move(right=0, absolute=True))
map('<end>', wdg.move(right=-1, absolute=True))
map('<tab>', wdg.tab())
map('<s-tab>', wdg.tab(-1))
map('<c-c>', wdg.close())
map('<CR>', '<c-j>', wdg.execute())
map('<F1>', lambda arg: arg.fm.display_command_help(arg.wdg))

map('<backspace>', wdg.delete(-1))
map('<delete>', wdg.delete(1))
map('<C-W>', wdg.delete_word())
map('<C-K>', wdg.delete_rest(1))
map('<C-U>', wdg.delete_rest(-1))
map('<C-Y>', wdg.paste())

def type_key(arg):
	log('x')
	arg.wdg.type_key(arg.match)
map('<any>', type_key)
log(map._tree)


# ===================================================================
# == Define direction keys
# ===================================================================
map = keymanager.get_context('directions')
map('<down>', dir=Direction(down=1))
map('<up>', dir=Direction(down=-1))
map('<left>', dir=Direction(right=-1))
map('<right>', dir=Direction(right=1))
map('<home>', dir=Direction(down=0, absolute=True))
map('<end>', dir=Direction(down=-1, absolute=True))
map('<pagedown>', dir=Direction(down=1, pages=True))
map('<pageup>', dir=Direction(down=-1, pages=True))
map('%<any>', dir=Direction(down=1, percentage=True, absolute=True))
map('<space>', dir=Direction(down=1, pages=True))
map('<CR>', dir=Direction(down=1))
