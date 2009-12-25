"""
List of allowed flags:
s: silent mode. output will be discarded.
d: detach the process.
p: redirect output to the pager

An uppercase key ensures that a certain flag will not be used.
"""
ALLOWED_FLAGS = 'sdpSDP'

class Applications(object):
	def get(self, app):
		"""Looks for an application, returns app_default if it doesn't exist"""
		try:
			return getattr(self, 'app_' + app)
		except AttributeError:
			return self.app_default

	def has(self, app):
		"""Returns whether an application is defined"""
		return hasattr(self, 'app_' + app)

	def all(self):
		"""Returns a list with all application functions"""
		return [x for x in self.__dict__ if x.startswith('app_')]

import os, sys
null = open(os.devnull, 'a')

def run(*args, **kw):
	"""Run files with the specified parameters"""
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
	popen_kw['stdout'] = sys.stderr

	for word in ('shell', 'stdout', 'stdin', 'stderr'):
		if word in kw:
			popen_kw[word] = kw[word]

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
		if fm.ui: fm.ui.suspend()
		p = Popen(args, **popen_kw)
		waitpid_no_intr(p.pid)
		if fm.ui: fm.ui.initialize()
		return p

def spawn(command, fm=None, suspend=True, wait=True):
	from subprocess import Popen, STDOUT
	from ranger.ext.waitpid_no_intr import waitpid_no_intr

	if suspend and fm and fm.ui:
		fm.ui.suspend()

	try:
		if fm and fm.stderr_to_out:
			process = Popen(command, shell=True, stderr=STDOUT)
		else:
			process = Popen(command, shell=True)
		if wait:
			waitpid_no_intr(process.pid)
	finally:
		if suspend and fm and fm.ui:
			fm.ui.initialize()
