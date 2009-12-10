ONE_KB = 1024
UNITS = 'BKMGTP'
MAX_EXPONENT = len(UNITS) - 1

def human_readable(byte):
	import math

	if not byte:
		return '0 B'

	exponent = int(math.log(byte, 2) / 10)
	flt = float(byte) / (1 << (10 * exponent))
	
	if exponent > MAX_EXPONENT:
		return '>9000' # off scale

	if int(flt) == flt:
		return '%.0f %s' % (flt, UNITS[exponent])

	else:
		return '%.2f %s' % (flt, UNITS[exponent])
