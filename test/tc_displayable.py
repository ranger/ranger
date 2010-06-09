# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import curses
from random import randint

from ranger.gui.displayable import Displayable, DisplayableContainer
from testlib import Fake, OK, raise_ok, TODO

class TestWithFakeCurses(unittest.TestCase):
	def setUp(self):
		self.win = Fake()
		self.fm = Fake()
		self.env = Fake()
		self.settings = Fake()
		self.initdict = {'win': self.win, 'settings': self.settings,
				'fm': self.fm, 'env': self.env}

		self.disp = Displayable(**self.initdict)
		self.disc = DisplayableContainer(**self.initdict)
		self.disc.add_child(self.disp)

		hei, wid = 100, 100
		self.env.termsize = (hei, wid)

	def tearDown(self):
		self.disp.destroy()
		self.disc.destroy()

	def test_colorscheme(self):
		# Using a color method implies change of window attributes
		disp = self.disp

		disp.win.chgat = raise_ok
		disp.win.attrset = raise_ok

		self.assertRaises(OK, disp.color, 'a', 'b')
		self.assertRaises(OK, disp.color_at, 0, 0, 0, 'a', 'b')
		self.assertRaises(OK, disp.color_reset)

	def test_focused_object(self):
		d1 = Displayable(**self.initdict)
		d2 = DisplayableContainer(**self.initdict)
		for obj in (Displayable(**self.initdict) for x in range(5)):
			d2.add_child(obj)
		d3 = DisplayableContainer(**self.initdict)
		for obj in (Displayable(**self.initdict) for x in range(5)):
			d3.add_child(obj)

		for obj in (d1, d2, d3):
			self.disc.add_child(obj)

		d3.container[3].focused = True

		self.assertEqual(self.disc._get_focused_obj(), d3.container[3])

		d3.container[3].focused = False
		d2.container[0].focused = True

		self.assertEqual(self.disc._get_focused_obj(), d2.container[0])

gWin = None

class TestDisplayableWithCurses(unittest.TestCase):
	def setUp(self):
		global gWin
		if not gWin:
			gWin = curses.initscr()
		self.win = gWin
		curses.cbreak()
		curses.noecho()
		curses.start_color()
		curses.use_default_colors()

		self.fm = Fake()
		self.env = Fake()
		self.settings = Fake()
		self.initdict = {'win': self.win, 'settings': self.settings,
				'fm': self.fm, 'env': self.env}
		self.disp = Displayable(**self.initdict)
		self.disc = DisplayableContainer(**self.initdict)
		self.disc.add_child(self.disp)

		self.env.termsize = self.win.getmaxyx()

	def tearDown(self):
		self.disp.destroy()
		curses.nocbreak()
		curses.echo()
		curses.endwin()

	@TODO
	def test_boundaries(self):
		disp = self.disp
		hei, wid = self.env.termsize

		self.assertRaises(ValueError, disp.resize, 0, 0, hei + 1, wid)
		self.assertRaises(ValueError, disp.resize, 0, 0, hei, wid + 1)
		self.assertRaises(ValueError, disp.resize, -1, 0, hei, wid)
		self.assertRaises(ValueError, disp.resize, 0, -1, hei, wid)

		for i in range(1000):
			box = [int(randint(0, hei) * 0.2), int(randint(0, wid) * 0.2)]
			box.append(randint(0, hei - box[0]))
			box.append(randint(0, wid - box[1]))

			def in_box(y, x):
				return (y >= box[1] and y < box[1] + box[3]) and \
						(x >= box[0] and x < box[0] + box[2])

			disp.resize(*box)
			self.assertEqual(box, [disp.y, disp.x, disp.hei, disp.wid],
					"Resizing failed for some reason on loop " + str(i))

			for y, x in zip(range(10), range(10)):
				is_in_box = in_box(y, x)

				point1 = (y, x)
				self.assertEqual(is_in_box, point1 in disp)

				point2 = Fake()
				point2.x = x
				point2.y = y
				self.assertEqual(is_in_box, point2 in disp)

	def test_click(self):
		self.disp.click = raise_ok

		hei, wid = self.env.termsize

		for i in range(50):
			winwid = randint(2, wid-1)
			winhei = randint(2, hei-1)
			self.disc.resize(0, 0, hei, wid)
			self.disp.resize(0, 0, winhei, winwid)
			fakepos = Fake()

			fakepos.x = winwid - 2
			fakepos.y = winhei - 2
			self.assertRaises(OK, self.disc.click, fakepos)

			fakepos.x = winwid
			fakepos.y = winhei
			self.disc.click(fakepos)


if __name__ == '__main__':
	unittest.main()
