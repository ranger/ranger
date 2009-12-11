ALLOWED_FLAGS = 'sdpSDP'

class Applications(object):
	def get(self, app):
		try:
			return getattr(self, 'app_' + app)
		except AttributeError:
			return self.app_default

	def has(self, app):
		return hasattr(self, 'app_' + app)

	def all(self):
		return [x for x in self.__dict__ if x.startswith('app_')]

import os
null = open(os.devnull, 'a')

def run(*args, **kw):
	from subprocess import Popen
	from subprocess import PIPE
	from ranger.ext.waitpid_no_intr import waitpid_no_intr

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
		if fm.ui is not None: fm.ui.exit()
		p = Popen(args, **popen_kw)
		waitpid_no_intr(p.pid)
		if fm.ui is not None: fm.ui.initialize()
		return p
