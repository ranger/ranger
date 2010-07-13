
import stat
from ranger.gui.color import *
from ranger.ext.waitpid_no_intr import waitpid_no_intr
from subprocess import Popen, PIPE
from ranger.ext.fast_typetest import *

OTHERWISE = None

def get_color(is_selected, f):
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
	return fg, bg, attr


rows = ([-1, 1],   # [level, ratio]
		[0,  3],
		[1,  4])

def l(s):
	cf = s.cwd.current_file
	if cf.is_dir:
		return s.cd(cf.basename)
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
	'J': lambda s: move(s, 10),
	'K': lambda s: move(s, -10),
	'h': lambda s: s.cd('..'),
	'E': lambda s: run(s, 'vim', s.cwd.current_file.path),
	'i': lambda s: run(s, 'less', s.cwd.current_file.path),
	'l': l,
	'G': lambda s: s.move(len(s.cwd.files) - 1),
	'g': lambda s: setattr(s, 'keymap', g_keys),
	'd': lambda s: setattr(s, 'keymap', d_keys),
	'Q': lambda s: s.exit(),
}

g_keys_raw = {
	'g': lambda s: s.move(0),
	'h': lambda s: s.cd('~'),
	'u': lambda s: s.cd('/usr'),
	'/': lambda s: s.cd('/'),
	OTHERWISE: lambda s: None  # happens in any case. this breaks key chain
}

d_keys_raw = {
	'u': lambda s: run_less(s, 'du', '-h', '--apparent-size', '--max-depth=1'),
}

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
d_keys = dict((normalize_key(c), leave_keychain(fnc)) \
		for c, fnc in d_keys_raw.items())
keys = dict((normalize_key(c), fnc) for c, fnc in keys_raw.items())
