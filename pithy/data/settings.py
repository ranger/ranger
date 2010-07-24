# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# This software is licensed under the GNU GPLv3; see COPYING for details.

import stat
import os
import pithy
from curses.ascii import ctrl
from pithy.ext.color import *
from pithy.ext.human_readable import human_readable
from pithy.ext.fast_typetest import *
from pithy.gui import OTHERWISE

# ------------------------------------------------------------------
# Define variables
# ------------------------------------------------------------------
# status is a global variable set by pithy.  Abbreviate it with s:
s = status

FILE_LAUNCHER = 'rifle.py %f'
BOOKMARK_DIR = os.path.join(conf_dir(), 'bookmarks')
SHOW_DIRECTORY_SIZE = True

keybuffer = None
info_strings = {}

try: os.mkdir(BOOKMARK_DIR)
except OSError: pass

# ------------------------------------------------------------------
# Set hooks
# ------------------------------------------------------------------
HIDE_EXTENSIONS = 'bak', 'pyc', 'pyo', 'srt', 'swp'

def hook(fnc):
	setattr(status.hooks, fnc.__name__, fnc)  # override a hook

def hide_files(filename, path):
	if filename[0] == '.' or filename[-1] == '~':
		return False
	if filename[-3:] in HIDE_EXTENSIONS:
		return False
	return filename != 'lost+found'
status.hooks.filter = hide_files

def show_files(filename, path):
	return True

def toggle_hidden():
	hidden = (s.hooks.filter == hide_files)
	s.hooks.filter = show_files if hidden else hide_files
	s.reload()

@hook
def statusbar():
	if keybuffer is not None:
		return statusbar_prompt + keybuffer + '_'
	return None

# how should the filename be displayed?
@hook
def filename(basename, fileobj, level, width):
	if level != 0:
		return basename
	try:
		return (basename, info_strings[fileobj])
	except KeyError:
		if SHOW_DIRECTORY_SIZE and fileobj.is_dir:
			try:
				info_string = str(len(os.listdir(fileobj.path)))
			except:
				info_string = "?"
		else:
			info_string = human_readable(fileobj.stat.st_size)
		# let's cache the result for faster access
		info_strings[fileobj] = info_string
		return (basename, info_string)

@hook
def reload_hook():
	# clear the cache of the filename-hook
	info_strings.clear()

@hook
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
	elif stat.S_ISCHR(f.mode) or stat.S_ISBLK(f.mode):
		fg = yellow
		attr |= bold
	elif stat.S_ISSOCK(f.mode):
		fg = magenta
		attr |= bold
	elif stat.S_ISFIFO(f.mode):
		fg = yellow
	elif f.mode & stat.S_IXUSR:
		fg = green
		attr |= bold
	if f.is_link:
		fg = cyan
	if f.path in status.selection:
		fg = yellow
		attr |= bold
	return fg, bg, attr

# ------------------------------------------------------------------
# Define the keymap and functions used in the keymap
# ------------------------------------------------------------------
def break_keychain():
	global keybuffer
	keybuffer = None
	status.keymap = keys

def break_keychain_wrap(fnc):
	return lambda: break_keychain() or fnc()

def start_keychain(keymap, prompt=None):
	global keybuffer
	global statusbar_prompt
	if prompt:
		keybuffer = ""
		statusbar_prompt = prompt
	status.keymap = keymap

def normalize_key(c):
	try:
		return ord(c)
	except:
		return c

def enter_dir_or_run_file():
	cwd, cf = status.cwd, status.cwd.current_file
	if cf:
		if cf.is_dir:
			if cwd.path == BOOKMARK_DIR:
				return status.cd(os.path.realpath(cf.path))
			return status.cd(cf.path)
		status.launch(FILE_LAUNCHER)

def set_sort_mode(fnc):
	def function():
		if status.sort_key != fnc:
			status.sort_key = fnc
			status.reload()
	return function

def goto_newest_file():
	best = max(status.cwd.files, key=lambda f: f.stat.st_mtime)
	status.cwd.select_filename(best.path)
	status.sync_pointer()

keys = {
	'r': lambda: s.reload(),
	'j': lambda: s.move(s.cwd.pointer + 1),
	'k': lambda: s.move(s.cwd.pointer - 1),
	'd': lambda: s.move(s.cwd.pointer + 20),
	'u': lambda: s.move(s.cwd.pointer - 20),
	'h': lambda: s.cd('..'),
	'l': enter_dir_or_run_file,
	'c': goto_newest_file,
	'E': lambda: s.launch('vim %f'),
	'i': lambda: s.launch('(highlight --ansi %f 2> /dev/null || cat %f)'\
			'| less -R'),
	'G': lambda: s.move(len(s.cwd.files) - 1),
	'w': lambda: setattr(s, 'ls_l_mode', not s.ls_l_mode),
	'g': lambda: start_keychain(g_keys),
	'x': lambda: start_keychain(custom_keys),
	'`': lambda: s.cd(os.path.join(conf_dir(), 'bookmarks')),
	'm': lambda: start_keychain({OTHERWISE: create_bookmark},
			prompt='name bookmark: '),
	'f': lambda: start_keychain({OTHERWISE: find_mode}, prompt='find: '),
	'1': set_sort_mode(None),
	'2': set_sort_mode(lambda f: -f.stat.st_size),
	'3': set_sort_mode(lambda f: -f.stat.st_mtime),
	'q': lambda: s.exit(),
	' ': lambda: (s.toggle_select_file(s.cwd.current_file.path),
	              s.move(s.cwd.pointer + 1)),
	ctrl('h'): toggle_hidden,
}

# define some aliases:
keys["'"] = keys["`"]
keys["Q"] = keys["q"]
keys["J"] = keys["d"]
keys["K"] = keys["u"]
keys[ctrl("d")] = keys["d"]
keys[ctrl("u")] = keys["u"]

# normalize the keys. (Turns "A" into ord("A"); we need the ascii ord value.)
keys = dict((normalize_key(c), fnc) for c, fnc in keys.items())
status.keymap = keys

# ------------------------------------------------------------------
# Define key chains and input prompts
# ------------------------------------------------------------------

# Definition of the x[...] key chain
custom_keys = {
	ord('u'): lambda: [status.launch('du -h --apparent-size' \
	                       ' --max-depth=1 | less'),
	                   break_keychain()],
	ord('f'): lambda: [status.launch('df -h | less'), break_keychain()],
	OTHERWISE: lambda: break_keychain(),
}

# Definition of the g[...] key chain
def cd(path):
	return lambda: status.cd(path)

g_keys = {
	'g': lambda: s.move(0),
	'0': lambda: s.cd(s.origin),
	OTHERWISE: lambda: None  # this breaks key chain
}

for key, path in {
	'h': '~', 'u': '/usr', 'r': '/', 'm': '/media', 't': '/tmp',
}.items(): g_keys[key] = cd(path)

g_keys = dict((normalize_key(c), break_keychain_wrap(fnc)) \
		for c, fnc in g_keys.items())

# Definition of the prompt (m[...] and f[...] key chains):
def handle_prompt():
	global keybuffer
	try:
		chr_lastkey = chr(status.lastkey)
	except:
		if status.lastkey == curses.KEY_BACKSPACE:
			if not keybuffer: return break_keychain()
			keybuffer = keybuffer[:-1]
	else:
		if status.lastkey == 127:   # BACKSPACE
			if not keybuffer: return break_keychain()
			keybuffer = keybuffer[:-1]
		elif status.lastkey == 27:   # ESC
			break_keychain()
		elif status.lastkey == 21:   # ^U
			keybuffer = ""
		else:
			keybuffer += chr_lastkey

def find_mode():
	global keybuffer
	handle_prompt()
	if keybuffer is None:
		return break_keychain()
	count = 0
	for f in status.cwd.files:
		if keybuffer in f.basename.lower():
			count += 1
			if count == 1:
				status.cwd.select_filename(f.path)
				status.sync_pointer()
	if count <= 1:
		break_keychain()
		if count == 1:
			cf = status.cwd.current_file
			if cf.is_dir:
				status.cd(cf.path)

def create_bookmark():
	global keybuffer
	handle_prompt()
	if keybuffer is None:
		return break_keychain()
	if not keybuffer.strip():
		return
	if status.lastkey == 10:
		link_name = os.path.join(BOOKMARK_DIR, keybuffer.strip())
		try:
			os.symlink(status.cwd.path, link_name)
		except OSError:
			if os.path.islink(link_name):
				os.unlink(link_name)
				os.symlink(status.cwd.path, link_name)
		break_keychain()
