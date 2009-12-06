
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

class OpenStruct(object):
	def __init__(self, __dictionary=None, **__keywords):
		if __dictionary:
			self.__dict__.update(__dictionary)
		if __keywords:
			self.__dict__.update(keywords)

	def __getitem__(self, key):
		return self.__dict__[key]
	
	def __setitem__(self, key, value):
		self.__dict__[key] = value
		return value

	def __contains__(self, key):
		return key in self.__dict__

def get_all(dirname):
	import os
	lst = []
	for f in os.listdir(dirname):
		if f.endswith('.py') and not f.startswith('_'):
			lst.append(f [0:f.index('.')])
	return lst


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

def waitpid_no_intr(pid):
	import os, errno

	while True:
		try:
			return os.waitpid(pid, 0)
		except OSError as e:
			if e.errno == errno.EINTR:
				continue
			else:
				raise

import os
null = open(os.devnull, 'a')

def popen(*args, **kw):
	from subprocess import Popen
	from subprocess import PIPE

	flags, fm = kw['flags'], kw['fm']
	for flag in flags:
		if ord(flag) <= 90:
			bad = flag + flag.lower()
			flags = ''.join(c for c in flags if c not in bad)

	args = map(str, args)
	popen_kw = {}

	if kw['stdin'] is not None:
		popen_kw['stdin'] = kw['stdin']

	if 's' in flags or 'd' in flags:
		popen_kw['stdout'] = popen_kw['stderr'] = popen_kw['stdin'] = null
	
	if 'p' in flags:
		popen_kw['stdout'] = PIPE
		p1 = Popen(args, **popen_kw)
		kw['stdin'] = p1.stdout
		kw['files'] = ()
		kw['flags'] = ''.join(f for f in kw['flags'] if f in 'd')
		p2 = kw['apps'].app_pager(**kw)
		return p2
	if 'd' in flags:
		p = Popen(args, **popen_kw)
		return p
	else:
		fm.ui.exit()
		p = Popen(args, **popen_kw)
		waitpid_no_intr(p.pid)
		fm.ui.initialize()
		return p
