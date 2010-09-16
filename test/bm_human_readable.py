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

import os.path
import sys
rangerpath = os.path.join(os.path.dirname(__file__), '..')
if sys.path[1] != rangerpath:
	sys.path[1:1] = [rangerpath]

from ranger.ext.human_readable import *

# The version before 2010/06/24:
import math
UNITS = 'BKMGTP'
MAX_EXPONENT = len(UNITS) - 1
def human_readable_old(byte, seperator=' '):
	if not byte:
		return '0'

	exponent = int(math.log(byte, 2) / 10)
	flt = round(float(byte) / (1 << (10 * exponent)), 2)

	if exponent > MAX_EXPONENT:
		return '>9000' # off scale

	if int(flt) == flt:
		return '%.0f%s%s' % (flt, seperator, UNITS[exponent])

	else:
		return '%.2f%s%s' % (flt, seperator, UNITS[exponent])

class benchmark_human_readable(object):
	def bm_current(self, n):
		for i in range(n):
			human_readable((128 * i) % 2**50)

	def bm_old(self, n):
		for i in range(n):
			human_readable_old((128 * i) % 2**50)
