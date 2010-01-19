# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

ONE_KB = 1024
UNITS = 'BKMGTP'
MAX_EXPONENT = len(UNITS) - 1

def human_readable(byte, seperator=' '):
	import math

	if not byte:
		return '0'

	exponent = int(math.log(byte, 2) / 10)
	flt = float(byte) / (1 << (10 * exponent))
	
	if exponent > MAX_EXPONENT:
		return '>9000' # off scale

	if int(flt) == flt:
		return '%.0f%s%s' % (flt, seperator, UNITS[exponent])

	else:
		return '%.2f%s%s' % (flt, seperator, UNITS[exponent])
