import curses
import _curses
from curses import color_pair
from ranger.gui.color import *

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
			safechgat(y, b.x, b.wid, attr | color_pair(get_color(fg, bg)))

	while True:
		hei, wid = win.getmaxyx()
		cwd = status.cwd
		cf = cwd.current_file

		# -------------------------
		# draw ui
		win.erase()

		# titlebar
		username = 'hut'
		hostname = 'debatom'
		start = username + '@' + hostname + ':'
		mid = start + status.cwd.path
		safeaddnstr(0, 0, mid + '/' + cf.basename, wid)
		safechgat(0, 0, -1, bold | color_pair(get_color(blue, -1)))
		safechgat(0, 0, len(start), bold | color_pair(get_color(green, -1)))
		safechgat(0, len(mid), -1, bold | color_pair(get_color(white, -1)))

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
		username = 'hut'
		hostname = 'debatom'
		start = username + '@' + hostname + ':'
		mid = start + status.cwd.path
		safeaddnstr(hei-1, 0, mid + '/' + cf.basename, wid)
		safechgat(hei-1, 0, -1, bold | color_pair(get_color(blue, -1)))
		safechgat(hei-1, 0, len(start), bold | color_pair(get_color(green, -1)))
		safechgat(hei-1, len(mid), -1, bold | color_pair(get_color(white, -1)))

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
