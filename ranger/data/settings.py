import stat
from ranger.ext.color import *
from ranger.ext.waitpid_no_intr import waitpid_no_intr
from subprocess import Popen, PIPE
from ranger.ext.fast_typetest import *
from curses.ascii import ctrl
import ranger

s = status

OTHERWISE = None

ALLOWED_BOOKMARKS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
		"abcdefghijklmnopqrstuvwxyz0123456789`'")

def get_color(f, context):
	fg, bg, attr = default, default, normal
	ext = f.extension.lower()
	if context.selected:
		attr = reverse
	if f.is_dir:
		fg = blue
		attr |= bold
	elif is_image(ext):
		fg = yellow
	elif is_video(ext) or is_audio(ext):
		fg = magenta
	elif is_container(ext):
		fg = red
	elif f.stat.st_mode & stat.S_IXUSR:
		fg = green
		attr |= bold
	if f.is_link:
		fg = cyan
	if f.path in status.selection:
		fg = yellow
		attr |= bold
	if status.ls_l_mode and attr & bold:
		attr ^= bold
	return fg, bg, attr

status.get_color = get_color

status.rows = ([-1, 1],
               [ 0, 3],
               [ 1, 4])

def hide_files(filename):
	if filename[0] == '.':
		return False
	return filename != 'lost+found'

def show_files(filename):
	return filename != 'lost+found'

def toggle_hidden():
	s.filter = show_files if s.filter == hide_files else hide_files
	s.reload()

status.filter = hide_files

def enter_dir_or_run_file():
	cf = s.cwd.current_file
	if cf:
		if cf.is_dir:
			return s.cd(cf.path)
		run('rifle.py', cf.basename)

def run(*args):
	s.curses_off()
	p = Popen(args)
	waitpid_no_intr(p.pid)
	s.curses_on()

def run_less(*args):
	s.curses_off()
	p = Popen(args, stdout=PIPE)
	p2 = Popen('less', stdin=p.stdout)
	waitpid_no_intr(p2.pid)
	s.curses_on()

keys_raw = {
	'r': lambda: s.reload(),
	'j': lambda: s.move(s.cwd.pointer + 1),
	'k': lambda: s.move(s.cwd.pointer - 1),
	'd': lambda: s.move(s.cwd.pointer + 20),
	'u': lambda: s.move(s.cwd.pointer - 20),
	'h': lambda: s.cd('..'),
	'l': enter_dir_or_run_file,
	'E': lambda: run('vim', s.cwd.current_file.path),
	'i': lambda: run('less', s.cwd.current_file.path),
	'G': lambda: s.move(len(s.cwd.files) - 1),
	'w': lambda: setattr(s, 'ls_l_mode', not s.ls_l_mode),
	'g': lambda: setattr(s, 'keymap', g_keys),
	'm': lambda: (setattr(s, 'draw_bookmarks', True),
	              setattr(s, 'keymap', set_bookmark_handler)),
	'`': lambda: (setattr(s, 'draw_bookmarks', True),
	              setattr(s, 'keymap', go_bookmark_handler)),
	'x': lambda: setattr(s, 'keymap', custom_keys),
	'f': lambda: (setattr(s, 'keymap', find_keys),
	              setattr(s, 'keybuffer', "")),
	'Q': lambda: s.exit(),
	' ': lambda: (s.toggle_select_file(s.cwd.current_file.path),
	              move(s, 1)),
	ctrl('h'): toggle_hidden,
}

keys_raw["'"] = keys_raw["`"]
keys_raw["q"] = keys_raw["Q"]
keys_raw["Z"] = keys_raw["Q"]
keys_raw["s"] = keys_raw["Q"]
keys_raw["J"] = keys_raw["d"]
keys_raw["K"] = keys_raw["u"]

g_keys_raw = {
	'g': lambda: s.move(0),
	OTHERWISE: lambda: None  # this breaks key chain
}

def cd(path):
	return lambda: status.cd(path)

for key, path in {
		'h': '~', 'u': '/usr', 'r': '/', 'm': '/media',
}.items(): g_keys_raw[key] = cd(path)

custom_keys_raw = {
	'u': lambda: run_less('du', '-h', '--apparent-size', '--max-depth=1'),
	'f': lambda: run_less('df', '-h'),
	OTHERWISE: lambda: None  # this breaks key chain
}


def _bookmark_key():
	status.keymap = keys
	status.draw_bookmarks = False
	try:
		key = chr(status.lastkey)
		assert key in ALLOWED_BOOKMARKS
	except:
		return
	if key == '`':
		key = "'"
	return key

def set_bookmark():
	status.set_bookmark(_bookmark_key(), status.cwd.path)

def go_bookmark():
	status.enter_bookmark(_bookmark_key())

go_bookmark_handler   = { OTHERWISE: go_bookmark }
set_bookmark_handler  = { OTHERWISE: set_bookmark }


def find_mode():
	try:
		status.keybuffer += chr(status.lastkey)
	except:
		pass
	count = 0
	for f in status.cwd.files:
		if status.keybuffer in f.basename.lower():
			count += 1
			if count == 1:
				status.cwd.select_filename(f.path)
	if count <= 1:
		status.keybuffer = None
		status.keymap = keys
		if count == 1:
			cf = status.cwd.current_file
			if cf.is_dir:
				status.cd(cf.path)

find_keys = { OTHERWISE: find_mode }

def leave_keychain(fnc):
	def new_fnc():
		status.keymap = keys
		return fnc()
	return new_fnc

def normalize_key(c):
	try:
		return ord(c)
	except:
		return c

g_keys = dict((normalize_key(c), leave_keychain(fnc)) \
		for c, fnc in g_keys_raw.items())
custom_keys = dict((normalize_key(c), leave_keychain(fnc)) \
		for c, fnc in custom_keys_raw.items())
keys = dict((normalize_key(c), fnc) for c, fnc in keys_raw.items())
status.keymap = keys
