import curses
from ranger.gui.color import *

class Bounds(object):
	def __init__(self, **kw):
		self.__dict__ = kw

def ui(win, status):
	curses.use_default_colors()
	curses.curs_set(0)

	def draw(level, directory, bounds):
		if directory.files is None:
			return
		for i, f in enumerate(directory.files):
			y = i + bounds.y
			if y >= bounds.hei:
				break
			win.addnstr(y, bounds.x, f.basename, bounds.wid)
			if i + directory.scroll_begin == directory.pointer:
				win.chgat(y, bounds.x, bounds.wid, reverse)

	while True:
		hei, wid = win.getmaxyx()

		# -------------------------
		# draw shit
		win.erase()
		ratiosum = float(sum(row[1] for row in status.rows))
		lastx = 0
		for i, row in enumerate(status.rows):
			level, ratio = row
			directory = status.get_level(level)
			rowwid = int(ratio / ratiosum * wid) - 1
			if directory:
				directory.load()
				draw(level, directory, Bounds(x=lastx,y=1,wid=rowwid,hei=hei))
			lastx += rowwid + 1

		# -------------------------
		# get char
		c = win.getch()
		try: action = status.keymap[c]
		except:
			try: action = status.keymap[None]
			except: continue
		action(status)
