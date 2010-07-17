import stat
import os
from ranger.gui import OTHERWISE
from ranger.ext.color import *
from ranger.ext.waitpid_no_intr import waitpid_no_intr
from subprocess import Popen, PIPE
from ranger.ext.fast_typetest import *
from curses.ascii import ctrl
import ranger

# ------------------------------------------------------------------
# Define variables
# ------------------------------------------------------------------
# status is a global variable set by ranger.  Abbreviate it with s:
s = status

ALLOWED_BOOKMARKS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ" \
		"abcdefghijklmnopqrstuvwxyz0123456789`'")

# ------------------------------------------------------------------
# Set hooks
# ------------------------------------------------------------------
HIDE_EXTENSIONS = '~', 'bak', 'pyc', 'pyo', 'swp'

def hide_files(filename, path):
	if filename[0] == '.':
		return False
	if any(filename.endswith(ext) for ext in HIDE_EXTENSIONS):
		return False
	return filename != 'lost+found'
status.hooks.filter = hide_files

def statusbar():
	if status.keybuffer is not None:
		return "find: " + status.keybuffer
	return None
status.hooks.statusbar = statusbar

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
	elif stat.S_ISCHR(f.stat.st_mode) or stat.S_ISBLK(f.stat.st_mode):
		fg = yellow
		attr |= bold
	elif stat.S_ISSOCK(f.stat.st_mode):
		fg = magenta
		attr |= bold
	elif stat.S_ISFIFO(f.stat.st_mode):
		fg = yellow
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
status.hooks.get_color = get_color

# ------------------------------------------------------------------
# Define the keymap and functions used in the keymap
# ------------------------------------------------------------------
def show_files(filename, path):
	return True

def toggle_hidden():
	s.hooks.filter = show_files if s.hooks.filter == hide_files else hide_files
	s.reload()

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
	              s.move(s.cwd.pointer + 1)),
	ctrl('h'): toggle_hidden,
}

keys_raw["'"] = keys_raw["`"]
keys_raw["q"] = keys_raw["Q"]
keys_raw["Z"] = keys_raw["Q"]
keys_raw["s"] = keys_raw["Q"]
keys_raw["J"] = keys_raw["d"]
keys_raw["K"] = keys_raw["u"]
keys_raw["/"] = keys_raw["f"]

g_keys_raw = {
	'g': lambda: s.move(0),
	'0': lambda: s.cd(s.origin),
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
