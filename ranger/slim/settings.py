
import stat
from ranger.gui.color import *
from ranger.ext.waitpid_no_intr import waitpid_no_intr
from subprocess import Popen, PIPE
from ranger.ext.fast_typetest import *

OTHERWISE = None

ALLOWED_BOOKMARKS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
		"abcdefghijklmnopqrstuvwxyz0123456789`'")

def get_color(status, is_selected, f):
	fg, bg, attr = default_colors
	ext = f.extension.lower()
	if is_selected:
		attr |= reverse
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
	return fg, bg, attr


rows = ([-1, 1],
        [ 0, 3],
        [ 1, 4])

def enter_dir_or_run_file(s):
	cf = s.cwd.current_file
	if cf:
		if cf.is_dir:
			return s.cd(cf.path)
		run(s, 'rifle.py', cf.basename)

def run(s, *args):
	s.curses_off()
	p = Popen(args)
	waitpid_no_intr(p.pid)
	s.curses_on()

def run_less(s, *args):
	s.curses_off()
	p = Popen(args, stdout=PIPE)
	p2 = Popen('less', stdin=p.stdout)
	waitpid_no_intr(p2.pid)
	s.curses_on()

def move(s, n):
	s.move(max(0, min(len(s.cwd.files) - 1, s.cwd.pointer + n)))

keys_raw = {
	'r': lambda s: s.reload(),
	'j': lambda s: move(s, 1),
	'k': lambda s: move(s, -1),
	'd': lambda s: move(s, 20),
	'u': lambda s: move(s, -20),
	'J': lambda s: move(s, 10),
	'K': lambda s: move(s, -10),
	'h': lambda s: s.cd('..'),
	'l': enter_dir_or_run_file,
	'E': lambda s: run(s, 'vim', s.cwd.current_file.path),
	'i': lambda s: run(s, 'less', s.cwd.current_file.path),
	'G': lambda s: s.move(len(s.cwd.files) - 1),
	'w': lambda s: setattr(s, 'ls_l_mode', not s.ls_l_mode),
	'g': lambda s: setattr(s, 'keymap', g_keys),
	'm': lambda s: (setattr(s, 'draw_bookmarks', True),
	                setattr(s, 'keymap', set_bookmark_handler)),
	'`': lambda s: (setattr(s, 'draw_bookmarks', True),
	                setattr(s, 'keymap', go_bookmark_handler)),
	'x': lambda s: setattr(s, 'keymap', custom_keys),
	'f': lambda s: (setattr(s, 'keymap', find_keys),
	                setattr(s, 'keybuffer', "")),
	'Q': lambda s: s.exit(),
	' ': lambda s: (s.toggle_select_file(s.cwd.current_file.path),
	                move(s, 1)),
}

keys_raw["'"] = keys_raw["`"]
keys_raw["s"] = keys_raw["Q"]

g_keys_raw = {
	'g': lambda s: s.move(0),
	'h': lambda s: s.cd('~'),
	'u': lambda s: s.cd('/usr'),
	'/': lambda s: s.cd('/'),
	OTHERWISE: lambda s: None  # this breaks key chain
}

custom_keys_raw = {
	'u': lambda s: run_less(s, 'du', '-h', '--apparent-size', '--max-depth=1'),
	'f': lambda s: run_less(s, 'df', '-h'),
	OTHERWISE: lambda s: None  # this breaks key chain
}


def bookmark(status, do):
	status.keymap = keys
	status.draw_bookmarks = False
	try:
		key = chr(status.lastkey)
	except:
		return
	if key not in ALLOWED_BOOKMARKS:
		return
	if key == '`':
		key = "'"
	if do == 'go':
		status.enter_bookmark(key)
	elif do == 'set':
		status.set_bookmark(key, status.cwd.path)

go_bookmark_handler   = { OTHERWISE: lambda s: bookmark(s, do='go') }
set_bookmark_handler  = { OTHERWISE: lambda s: bookmark(s, do='set') }


def find_mode(status):
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
	def new_fnc(status):
		status.keymap = keys
		return fnc(status)
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
