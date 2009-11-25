#!/usr/bin/python3
# coding=utf-8
# some tests with curses, threads and unicode
import os
import curses
import time
import locale

lock = _thread.allocate_lock()

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

blocked = False
stringy = 'るでか'
stdscr = curses.initscr()
#win1 = curses.newwin(

curses.noecho()
curses.cbreak()
curses.halfdelay(3)
stdscr.keypad(1)
#curses.curs_set(0)

stdscr.addstr(4, 0, stringy)
stdscr.refresh()

class ThreadTest(threading.Thread):
	def __init__(self, *a, **b):
		threading.Thread.__init__(self, *a, **b)
		self.killed = False

	def run(self):
		global stdscr
		global blocked
		for i in range(1,50):
			while blocked: time.sleep(0.1)
			blocked = True
			stdscr.addstr(1, 0, str(i))
			stdscr.refresh()
			blocked = False
			time.sleep(0.1)
			if self.killed: raise SystemExit()

	def kill(self):
		self.killed = True

thr = ThreadTest()
thr.start()

try:
	while 1:
		c = stdscr.getch()
		if c == ord('q'): raise
		while blocked: time.sleep(0.1)
		blocked = True
		stdscr.addstr(0, 0, str(c))
		stdscr.refresh()
		blocked = False

except Exception:
	thr.kill()
	raise
finally:
	curses.nocbreak()
	stdscr.keypad(1)
	curses.echo()
	curses.endwin()
#	curses.curs_set(1)

