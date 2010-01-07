if __name__ == '__main__': from __init__ import init; init()

from unittest import TestCase, main

class Test(TestCase):
	def test_wrapper(self):
		from ranger.keyapi import Wrapper

		class dummyfm(object):
			def move(relative):
				return "I move down by {0}".format(relative)

		class commandarg(object):
			def __init__(self):
				self.fm = dummyfm
				self.n = None

		arg = commandarg()

		do = Wrapper('fm')
		command = do.move(relative=4)

		self.assertEqual(command(arg), 'I move down by 4')

if __name__ == '__main__': main()
