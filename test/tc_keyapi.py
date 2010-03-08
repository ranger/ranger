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

class Test(TestCase):
	def test_wrapper(self):
		from ranger.api.keys import Wrapper

		class dummyfm(object):
			def move(self, relative):
				return "I move down by {0}".format(relative)

		class commandarg(object):
			def __init__(self):
				self.fm = dummyfm()
				self.n = None

		arg = commandarg()

		do = Wrapper('fm')
		command = do.move(relative=4)

		self.assertEqual(command(arg), 'I move down by 4')

if __name__ == '__main__': main()
