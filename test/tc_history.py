if __name__ == '__main__': from __init__ import init; init()

from ranger.container import History
from unittest import TestCase, main
import unittest

class Test(TestCase):
	def test_history(self):
		hist = History(3)
		for i in range(6):
			hist.add(i)
		self.assertEqual([3,4,5], list(hist))

		hist.back()

		self.assertEqual(4, hist.current())
		self.assertEqual([3,4], list(hist))

		self.assertEqual(5, hist.top())

		hist.back()
		self.assertEqual(3, hist.current())
		self.assertEqual([3], list(hist))

		# no change if current == bottom
		self.assertEqual(hist.current(), hist.bottom())
		last = hist.current()
		hist.back()
		self.assertEqual(hist.current(), last)

		self.assertEqual(5, hist.top())

		hist.forward()
		hist.forward()
		self.assertEqual(5, hist.current())
		self.assertEqual([3,4,5], list(hist))


		self.assertEqual(3, hist.bottom())
		hist.add(6)
		self.assertEqual(4, hist.bottom())
		self.assertEqual([4,5,6], list(hist))

if __name__ == '__main__': main()
