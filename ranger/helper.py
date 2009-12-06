
LOGFILE = '/tmp/errorlog'

def log(txt):
	f = open(LOGFILE, 'a')
	f.write("r1: ")
	f.write(str(txt))
	f.write("\n")
	f.close()

class OpenStruct(object):
	def __init__(self, __dictionary=None, **__keywords):
		if __dictionary:
			self.__dict__.update(__dictionary)
		if __keywords:
			self.__dict__.update(__keywords)

	def __getitem__(self, key):
		return self.__dict__[key]
	
	def __setitem__(self, key, value):
		self.__dict__[key] = value
		return value

	def __contains__(self, key):
		return key in self.__dict__

# used to get all colorschemes in ~/.ranger/colorschemes and ranger/colorschemes
def get_all(dirname):
	import os
	result = []
	for filename in os.listdir(dirname):
		if filename.endswith('.py') and not filename.startswith('_'):
			result.append(filename[0:filename.index('.')])
	return result


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

def waitpid_no_intr(pid):
	""" catch interrupts which occur while using os.waitpid """
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
		process1 = Popen(args, **popen_kw)
		kw['stdin'] = process1.stdout
		kw['files'] = ()
		kw['flags'] = ''.join(f for f in kw['flags'] if f in 'd')
		process2 = kw['apps'].app_pager(**kw)
		return process2
	if 'd' in flags:
		process = Popen(args, **popen_kw)
		return process
	else:
		fm.ui.exit()
		p = Popen(args, **popen_kw)
		waitpid_no_intr(p.pid)
		fm.ui.initialize()
		return p
