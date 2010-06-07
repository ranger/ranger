#!/usr/bin/python
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

"""Run all the tests inside the test/ directory as a test suite."""
if __name__ == '__main__':
	import unittest
	import sys
	import os

	try:
		verbosity = int(sys.argv[1])
	except IndexError:
		verbosity = 2

	ls = os.listdir(sys.path[0])
	paths = [p[:-3] for p in ls if p[:3] == 'tc_' and p[-3:] == '.py']
	suite = unittest.TestLoader().loadTestsFromNames(paths)
	result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
	if len(result.errors) + len(result.failures) > 0:
		sys.exit(1)
