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
