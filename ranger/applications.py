"""
List of allowed flags:
s: silent mode. output will be discarded.
d: detach the process.
p: redirect output to the pager

An uppercase key ensures that a certain flag will not be used.
"""

import os, sys
from ranger.ext.waitpid_no_intr import waitpid_no_intr
from subprocess import Popen, PIPE

devnull = open(os.devnull, 'a')

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
		methods = self.__class__.__dict__
		return [meth[4:] for meth in methods if meth.startswith('app_')]

class AppContext(object):
	def __init__(self, app='default', files=None, mode=0, flags='', fm=None,
			stdout=None, stderr=None, stdin=None, shell=None,
			wait=True, action=None):

		if files is None:
			self.files = []
		else:
			self.files = list(files)

		try:
			self.file = self.files[0]
		except IndexError:
			self.file = None

		self.app = app
		self.action = action
		self.mode = mode
		self.flags = flags
		self.fm = fm
		self.stdout = stdout
		self.stderr = stderr
		self.stdin = stdin
		self.wait = wait

		if shell is None:
			self.shell = isinstance(action, str)
		else:
			self.shell = shell
	
	def __getitem__(self, key):
		return self.files[key]
	
	def __iter__(self):
		if self.files:
			for f in self.files:
				yield f.path
	
	def squash_flags(self):
		for flag in self.flags:
			if ord(flag) <= 90:
				bad = flag + flag.lower()
				self.flags = ''.join(c for c in self.flags if c not in bad)

	def get_action(self, apps=None):
		if apps is None and self.fm:
			apps = self.fm.apps

		if apps is None:
			raise RuntimeError("AppContext has no source for applications!")

		app = apps.get(self.app)
		self.action = app(self)
		self.shell = isinstance(self.action, str)
	
	def run(self):
		self.squash_flags()
		if self.action is None:
			self.get_action()

		# ---------------------------- determine keywords for Popen()

		kw = {}
		kw['stdout'] = sys.stderr
		kw['stderr'] = sys.stderr
		kw['args'] = self.action

		for word in ('shell', 'stdout', 'stdin', 'stderr'):
			if getattr(self, word) is not None:
				kw[word] = getattr(self, word)

		if 's' in self.flags or 'd' in self.flags:
			kw['stdout'] = kw['stderr'] = kw['stdin'] = devnull

		# --------------------------- run them
		if 'p' in self.flags:
			kw['stdout'] = PIPE
			kw['stderr'] = PIPE
			process1 = Popen(**kw)
			process2 = run(app='pager', stdin=process1.stdout, fm=self.fm)
			return process2

		elif 'd' in self.flags:
			process = Popen(**kw)
			return process

		else:
			self._activate_ui(False)
			try:
				p = Popen(**kw)
				if self.wait:
					waitpid_no_intr(p.pid)
			finally:
				self._activate_ui(True)

	def _activate_ui(self, boolean):
		if self.fm and self.fm.ui:
			if boolean:
				self.fm.ui.initialize()
			else:
				self.fm.ui.suspend()

def run(action=None, **kw):
	app = AppContext(action=action, **kw)
	return app.run()

def tup(*args):
	return tuple(args)
