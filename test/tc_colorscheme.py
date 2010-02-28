if __name__ == '__main__': from __init__ import init; init()

from unittest import TestCase, main
import random
import ranger.colorschemes
from ranger.gui.colorscheme import ColorScheme
from ranger.gui.context import CONTEXT_KEYS

class Test(TestCase):
	def setUp(self):
		import random
		schemes = []
		for key, mod in vars(ranger.colorschemes).items():
			if type(mod) == type(random):
				for key, var in vars(mod).items():
					if type(var) == type and issubclass(var, ColorScheme) \
							and var != ColorScheme:
						schemes.append(var)
		self.schemes = set(schemes)

	def test_colorschemes(self):
		def test(scheme):
			scheme.get()  # test with no arguments

			for i in range(300):  # test with a bunch of random (valid) arguments
				sample = random.sample(CONTEXT_KEYS, random.randint(2, 9))
				scheme.get(*sample)

		for scheme in self.schemes:
			test(scheme())

if __name__ == '__main__': main()
