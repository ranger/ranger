import curses
import _curses
from ranger.gui.color import *
from pwd import getpwuid
from grp import getgrgid
from os import getuid, readlink
from time import time, strftime, localtime

def clr(fg, bg):
	return curses.color_pair(get_color(fg, bg))

class Bounds(object):
	def __init__(self, **kw):
		self.__dict__ = kw

def ui(status):
	win = status.stdscr

	def safechgat(*args):
		try: win.chgat(*args)
		except _curses.error: pass

	def safeaddnstr(*args):
		try: win.addnstr(*args)
		except _curses.error: pass

	def draw(level, directory, bounds):
		b = bounds
		if directory.files is None:
			return
		for i in range(len(directory.files)):
			y = i + b.y
			actual_i = i + directory.scroll_begin
			if y >= b.y + b.hei:
				break
			try:
				f = directory.files[actual_i]
			except:
				break
			safeaddnstr(y, b.x, f.basename, b.wid)
			is_selected = (actual_i == directory.pointer)
			fg, bg, attr = status.get_color(is_selected, f)
			safechgat(y, b.x, b.wid, attr | clr(fg, bg))

	while True:
		hei, wid = win.getmaxyx()
		cwd = status.cwd
		cf = cwd.current_file
		assert cf, cwd.files

		# -------------------------
		# draw ui
		win.erase()

		# titlebar
		username = 'hut'
		hostname = 'debatom'
		start = username + '@' + hostname + ':'
		mid = start + status.cwd.path
		safeaddnstr(0, 0, mid + '/' + cf.basename, wid)
		safechgat(0, 0, -1, bold | clr(blue, -1))
		safechgat(0, 0, len(start), bold | clr(green, -1))
		safechgat(0, len(mid), -1, bold | clr(white, -1))

		# columns
		ratiosum = float(sum(row[1] for row in status.rows))
		lastx = 0
		for i, row in enumerate(status.rows):
			level, ratio = row
			directory = status.get_level(level)
			rowwid = int(ratio / ratiosum * wid) - 1
			if directory:
				draw(level, directory,
						Bounds(x=lastx,y=1,wid=rowwid,hei=hei-2))
			lastx += rowwid + 1

		# statusbar
		perms = cf.permission_string
		y = hei - 1
		safeaddnstr(y, 0, cf.permission_string, -1)
		color = clr(cyan if getuid() == cf.stat.st_uid else magenta, -1)
		safechgat(y, 0, 10, color)
		if cf.is_link:
			try:    lastinfo = ' -> ' + readlink(cf.path)
			except: lastinfo = ' -> ?'
		else:
			lastinfo = strftime('%Y-%m-%d %H:%M', localtime(cf.stat.st_mtime))
		info = ' '.join([str(cf.stat.st_nlink),
			getpwuid(cf.stat.st_uid)[0],
			getgrgid(cf.stat.st_gid)[0],
			lastinfo])
		safeaddnstr(y, 11, info, -1)
		scroll_start = cwd.scroll_begin
		max_pos = len(cwd.files) - hei - 2
		if max_pos < 0:
			shown = 'All'
		elif scroll_start == 0:
			shown = 'Top'
		elif scroll_start >= max_pos:
			shown = 'Bot'
		else:
			shown = '{0:0>.0f}%'.format(100.0 * scroll_start / max_pos)
		pos = str(cwd.pointer + 1) + '/' + str(len(cwd.files))

		right = '  '.join((pos, shown))
		safeaddnstr(y, wid - len(right), right, len(right))

		# -------------------------
		# handle input
		c = win.getch()
		if c == curses.KEY_RESIZE:
			status.move(status.cwd.pointer)
		else:
			try: action = status.keymap[c]
			except:
				try: action = status.keymap[None]
				except: continue
			action(status)
