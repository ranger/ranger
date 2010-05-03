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
	from test import *
	from time import time
	from types import FunctionType as function
	from sys import argv
	bms = []
	try:
		n = int(argv[1])
	except IndexError:
		n = 10
	for key, val in vars().copy().items():
		if key.startswith('bm_'):
			bms.extend(v for k,v in vars(val).items() if type(v) == type)
	for bmclass in bms:
		for attrname in vars(bmclass):
			if not attrname.startswith('bm_'):
				continue
			bmobj = bmclass()
			t1 = time()
			method = getattr(bmobj, attrname)
			methodname = "{0}.{1}".format(bmobj.__class__.__name__, method.__name__)
			try:
				method(n)
			except:
				print("{0} failed!".format(methodname))
				raise
			else:
				t2 = time()
				print("{0:60}: {1:10}s".format(methodname, t2 - t1))
