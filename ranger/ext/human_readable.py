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

import math

ONE_KB = 1024
UNITS = 'BKMGTP'
MAX_EXPONENT = len(UNITS) - 1

def human_readable(byte, seperator=' '):
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
