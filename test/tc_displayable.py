if __name__ == '__main__': from __init__ import init; init()

import unittest
import curses
from random import randint

from ranger.gui.displayable import\
		Displayable, DisplayableContainer, OutOfBoundsException
from test import Fake, OK, raise_ok

class TestDisplayable(unittest.TestCase):
	def setUp(self):
		self.win = Fake()
		self.fm = Fake()
		self.env = Fake()
		self.settings = Fake()
		self.disp = Displayable( win=self.win,
				env=self.env, fm=self.fm, settings=self.settings)

		hei, wid = 100, 100
		self.env.termsize = (hei, wid)

	def tearDown(self):
		self.disp.destroy()

	def test_colorscheme(self):
		# Using a color method implies change of window attributes
		disp = self.disp

		self.win.chgat = raise_ok
		self.win.attrset = raise_ok

		self.assertRaises(OK, disp.color, 'a', 'b')
		self.assertRaises(OK, disp.color_at, 0, 0, 0, 'a', 'b')
		self.assertRaises(OK, disp.color_reset)

	def test_boundaries(self):
		disp = self.disp
		hei, wid = self.env.termsize

		self.assertRaises(OutOfBoundsException, disp.resize, 0, 0, hei + 1, wid)
		self.assertRaises(OutOfBoundsException, disp.resize, 0, 0, hei, wid + 1)
		self.assertRaises(OutOfBoundsException, disp.resize, -1, 0, hei, wid)
		self.assertRaises(OutOfBoundsException, disp.resize, 0, -1, hei, wid)

		box = (randint(10, 20), randint(30, 40), \
				randint(30, 40), randint(10, 20))

		def in_box(y, x):
			return (x >= box[1] and x < box[1] + box[3]) and \
					(y >= box[0] and y < box[0] + box[2])

		disp.resize(*box)
		for y, x in zip(range(10), range(10)):
			is_in_box = in_box(y, x)

			point1 = (y, x)
			self.assertEqual(is_in_box, point1 in disp)

			point2 = Fake()
			point2.x = x
			point2.y = y
			self.assertEqual(is_in_box, point2 in disp)

class TestDisplayableContainer(unittest.TestCase):
	def setUp(self):
		self.win = Fake()
		self.fm = Fake()
		self.env = Fake()
		self.settings = Fake()

		self.initdict = {'win': self.win, 'settings': self.settings,
				'fm': self.fm, 'env': self.env}

		self.disp = Displayable(**self.initdict)
		self.disc = DisplayableContainer(**self.initdict)
		self.disc.add_obj(self.disp)

		hei, wid = (100, 100)
		self.env.termsize = (hei, wid)

	def tearDown(self):
		self.disc.destroy()

	def test_container(self):
		self.assertTrue(self.disp in self.disc.container)

	def test_click(self):
		self.disp.click = raise_ok

		self.disc.resize(0, 0, 50, 50)
		self.disp.resize(0, 0, 20, 20)
		fakepos = Fake()

		fakepos.x = 10
		fakepos.y = 10
		self.assertRaises(OK, self.disc.click, fakepos)

		fakepos.x = 30
		fakepos.y = 10
		self.disc.click(fakepos)

	def test_focused_object(self):
		d1 = Displayable(**self.initdict)
		d2 = DisplayableContainer(**self.initdict)
		d2.add_obj(*[Displayable(**self.initdict) for x in range(5)])
		d3 = DisplayableContainer(**self.initdict)
		d3.add_obj(*[Displayable(**self.initdict) for x in range(5)])

		self.disc.add_obj(d1, d2, d3)

		d3.container[3].focused = True

		self.assertEqual(self.disc.get_focused_obj(), d3.container[3])

		d3.container[3].focused = False
		d2.container[0].focused = True

		self.assertEqual(self.disc.get_focused_obj(), d2.container[0])

if __name__ == '__main__':
	unittest.main()
