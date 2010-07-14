import curses
import _curses
from ranger.ext.human_readable import human_readable
from ranger.ext.color import *
from pwd import getpwuid
from grp import getgrgid
from os import getuid, readlink
from time import time, strftime, localtime

def clr(fg, bg):
	return curses.color_pair(get_color(fg, bg))

class Context(object):
	selected = False

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

	def draw_row(level, directory, bounds, info=False):
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
			if info:
				safeaddnstr(y, b.x, "%s%3d %s %s %6s %s %s" % (
					f.permission_string, f.stat.st_nlink,
					getpwuid(f.stat.st_uid)[0],
					getgrgid(f.stat.st_gid)[0],
					human_readable(f.stat.st_size),
					strftime('%b %d %H:%M', localtime(f.stat.st_mtime)),
					f.basename), b.wid)
			else:
				safeaddnstr(y, b.x, f.basename, b.wid)
			is_selected = (actual_i == directory.pointer)
			context = Context()
			context.selected = is_selected
			fg, bg, attr = status.get_color(f, context)
			safechgat(y, b.x, b.wid, attr | clr(fg, bg))

	def draw():
		# draw ui
		win.erase()

		# titlebar
		username = 'hut'
		hostname = 'debatom'
		start = username + '@' + hostname + ':'
		mid = start + status.cwd.path
		safeaddnstr(0, 0, mid + (cf and '/' + cf.basename or '/'), wid)
		safechgat(0, 0, -1, bold | clr(blue, -1))
		safechgat(0, 0, len(start), bold | clr(green, -1))
		safechgat(0, len(mid), -1, bold | clr(white, -1))

		# statusbar
		y = hei - 1
		if status.keybuffer is not None:
			safeaddnstr(y, 0, "find: " + status.keybuffer, wid)
		elif cf:
			perms = cf.permission_string
			safeaddnstr(y, 0, cf.permission_string, -1)
			color = clr(cyan if getuid() == cf.stat.st_uid else magenta, -1)
			safechgat(y, 0, 10, color)
			if cf.is_link:
				try:    lastinfo = ' -> ' + readlink(cf.path)
				except: lastinfo = ' -> ?'
			else:
				lastinfo = strftime('%Y-%m-%d %H:%M',
						localtime(cf.stat.st_mtime))
			info = ' '.join([str(cf.stat.st_nlink),
				getpwuid(cf.stat.st_uid)[0],
				getgrgid(cf.stat.st_gid)[0],
				lastinfo])
			safeaddnstr(y, 11, info, -1)
		if cf:
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
		else:
			right = "0/0  All"
			safeaddnstr(y, wid - len(right), right, len(right))

		if status.draw_bookmarks:
			# bookmarks
			status.load_bookmarks()
			y = 1
			for key in sorted(item for item in status.bookmarks):
				safeaddnstr(y, 1, key + ': ' + status.bookmarks[key], wid)
				y += 1
				if y > hei - 2:
					break

		elif status.ls_l_mode:
			draw_row(0, cwd, Bounds(x=0, y=1, wid=wid, hei=hei-2), info=True)

		else:
			# columns
			rows = status.rows
			if cf and not cf.is_dir and rows[-1][0] == 1:
				cut_off = sum(row[1] for row in rows if row[0] > 0)
				rows = [row for row in rows if row[0] <= 0]
				rows[-1] = [rows[-1][0], rows[-1][1] + cut_off]
			ratiosum = float(sum(row[1] for row in rows))
			lastx = 0
			for i, row in enumerate(rows):
				level, ratio = row
				directory = status.get_level(level)
				rowwid = int(ratio / ratiosum * wid)
				if directory:
					draw_row(level, directory,
							Bounds(x=lastx,y=1,wid=rowwid,hei=hei-2))
				lastx += rowwid + 1

	while True:
		hei, wid = win.getmaxyx()
		cwd = status.cwd
		cf = cwd.current_file

		# -------------------------
		draw()

		# -------------------------
		# handle input
		raise SystemExit()
		c = win.getch()
		status.lastkey = c
		if c == curses.KEY_RESIZE:
			status.move(status.cwd.pointer)
		else:
			try: action = status.keymap[c]
			except:
				try: action = status.keymap[None]
				except: continue
			action()
