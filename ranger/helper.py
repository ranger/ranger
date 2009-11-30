
LOGFILE = '/tmp/errorlog'

def log(txt):
	f = open(LOGFILE, 'a')
	f.write("r1: ")
	f.write(str(txt))
	f.write("\n")
	f.close()

ONE_KB = 1024
UNITS = tuple('BKMGTP')
NINE_THOUSAND = len(UNITS) - 1

def human_readable(byte):
	import math

	if not byte:
		return '0 B'

	its = int(math.log(byte, 2) / 10)
	flt = float(byte) / (1 << (10 * its))
	
	if its > NINE_THOUSAND:
		return '>9000' # off scale

	if int(flt) == flt:
		return '%.0f %s' % (flt, UNITS[its])

	else:
		return '%.2f %s' % (flt, UNITS[its])
