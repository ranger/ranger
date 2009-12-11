if __name__ == '__main__':
	from os.path import abspath, join
	import sys
	sys.path.append(abspath(join(sys.path[0], '..')))

from ranger.container import History
from unittest import TestCase, main
import unittest

class Test(TestCase):
	def test_everything(self):
		hist = History(3)
		for i in range(6):
			hist.add(i)
		self.assertEqual([3,4,5], list(hist))

		hist.back()

		self.assertEqual(4, hist.top())
		self.assertEqual([3,4], list(hist))

		hist.back()
		self.assertEqual(3, hist.top())
		self.assertEqual([3], list(hist))

		# no change if top == bottom
		self.assertEqual(hist.top(), hist.bottom())
		last_top = hist.top()
		hist.back()
		self.assertEqual(hist.top(), last_top)


		hist.forward()
		hist.forward()
		self.assertEqual(5, hist.top())
		self.assertEqual([3,4,5], list(hist))


		self.assertEqual(3, hist.bottom())
		hist.add(6)
		self.assertEqual(4, hist.bottom())
		self.assertEqual([4,5,6], list(hist))

if __name__ == '__main__': main()
