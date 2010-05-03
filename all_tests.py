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
	from test import *
	from sys import exit, argv

	try:
		verbosity = int(argv[1])
	except IndexError:
		verbosity = 2

	tests = []
	for key, val in vars().copy().items():
		if key.startswith('tc_'):
			tests.extend(v for k,v in vars(val).items() if type(v) == type)

	suite = unittest.TestSuite(map(unittest.makeSuite, tests))
	result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
	if len(result.errors) + len(result.failures) > 0:
		exit(1)
