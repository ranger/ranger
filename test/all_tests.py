#!/usr/bin/env python
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

"""
Run all the tests inside this directory as a test suite.
Usage: ./all_tests.py [verbosity]
"""

import os
import sys
import unittest

if __name__ == '__main__':
	verbosity = int(sys.argv[1]) if len(sys.argv) > 1 else 1
	tests     = (fname[:-3] for fname in os.listdir(sys.path[0]) \
	             if fname[:3] == 'tc_' and fname[-3:] == '.py')
	suite     = unittest.TestLoader().loadTestsFromNames(tests)
	result    = unittest.TextTestRunner(verbosity=verbosity).run(suite)
	if len(result.errors + result.failures) > 0:
		sys.exit(1)
