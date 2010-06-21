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
Run all the benchmarks inside this directory.
Usage: ./all_benchmarks.py [count] [regexp-filters...]
"""

import os
import re
import sys
import time

if __name__ == '__main__':
	count   = int(sys.argv[1]) if len(sys.argv) > 1 else 10
	regexes = [re.compile(fltr) for fltr in sys.argv[2:]]
	modules = (fname[:-3] for fname in os.listdir(sys.path[0]) \
			if fname[:3] == 'bm_' and fname[-3:] == '.py')

	def run_benchmark(cls, methodname):
		full_method_name = "{0}.{1}".format(cls.__name__, methodname)
		if all(re.search(full_method_name) for re in regexes):
			method = getattr(cls(), methodname)
			t1 = time.time()
			try:
				method(count)
			except:
				print("{0} failed!".format(full_method_name))
				raise
			else:
				t2 = time.time()
				print("{0:60}: {1:10}s".format(full_method_name, t2 - t1))

	for val in [__import__(module) for module in modules]:
		for cls in vars(val).values():
			if type(cls) == type:
				for methodname in vars(cls):
					if methodname.startswith('bm_'):
						run_benchmark(cls, methodname)
