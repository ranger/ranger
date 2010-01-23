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

"""
This module faciliates starting of new processes.
"""

import os, sys
from ranger.ext.waitpid_no_intr import waitpid_no_intr
from subprocess import Popen, PIPE
from ranger.ext.shell_escape import shell_escape
from ranger.ext.iter_tools import flatten
from ranger.shared import FileManagerAware

devnull = open(os.devnull, 'a')

ALLOWED_FLAGS = 'sdpSDP'

class Applications(FileManagerAware):
	"""
	This class contains definitions on how to run programs and should
	be extended in ranger.defaults.apps

	The user can decide what program to run, and if he uses eg. 'vim', the
	function app_vim() will be called.  However, usually the user
	simply wants to "start" the file without specific instructions.
	In such a case, app_default() is called, where you should examine
	the context and decide which program to use.

	All app functions have a name starting with app_ and return a string
	containing the whole command or a tuple containing a list of the
	arguments. They are supplied with one argument, which is the
	AppContext instance.

	You should define at least app_default, app_pager and app_editor since
	internal functions depend on those.  Here are sample implementations:

	def app_default(self, context):
		if context.file.media:
			if context.file.video:
				# detach videos from the filemanager
				context.flags += 'd'
			return self.app_mplayer(context)
		else:
			return self.app_editor(context)
	
	def app_pager(self, context):
		return ('less', ) + tuple(context)

	def app_editor(self, context):
		return ('vim', ) + tuple(context)
	"""

	def _meets_dependencies(self, fnc):
		try:
			deps = fnc.dependencies
		except AttributeError:
			return True

		for dep in deps:
			if hasattr(dep, 'dependencies') \
			and not self._meets_dependencies(dep):
				return False
			if dep not in self.fm.executables:
				return False

		return True

	def either(self, context, *args):
		for app in args:
			try:
				application_handler = getattr(self, 'app_' + app)
			except AttributeError:
				continue
			if self._meets_dependencies(application_handler):
				return application_handler(context)

	def app_self(self, context):
		"""Run the file itself"""
		return "./" + context.file.basename

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
	"""
	An AppContext object abstracts the spawning of processes.

	At initialization of the object you can define many high-level options.
	When you call the run() function, those options are evaluated and
	translated into Popen() calls.

	An instances of this class is passed as the only argument to
	app_xyz calls of the Applications object.
	
	Attributes:
	action -- a string with a command or a list of arguments for
		the Popen call.
	app -- the name of the app function. ("vim" for app_vim.)
		app is used to get an action if the user didn't specify one.
	mode -- a number, mainly used in determining the action in app_xyz()
	flags -- a string with flags which change the way programs are run
	files -- a list containing files, mainly used in app_xyz
	file -- an arbitrary file from that list (or None)
	fm -- the filemanager instance
	wait -- boolean, wait for the end or execute programs in parallel?
	stdout -- directly passed to Popen
	stderr -- directly passed to Popen
	stdin -- directly passed to Popen
	shell -- directly passed to Popen. Should the string be shell-interpreted?

	List of allowed flags:
	s: silent mode. output will be discarded.
	d: detach the process.
	p: redirect output to the pager

	An uppercase key ensures that a certain flag will not be used.
	"""

	def __init__(self, app='default', files=None, mode=0, flags='', fm=None,
			stdout=None, stderr=None, stdin=None, shell=None,
			wait=True, action=None):
		"""
		The necessary parameters are fm and action or app.
		"""

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
	
	def __iter__(self):
		"""Iterates over all file paths"""
		if self.files:
			for f in self.files:
				yield f.path
	
	def squash_flags(self):
		"""Remove duplicates and lowercase counterparts of uppercase flags"""
		for flag in self.flags:
			if ord(flag) <= 90:
				bad = flag + flag.lower()
				self.flags = ''.join(c for c in self.flags if c not in bad)

	def get_action(self, apps=None):
		"""Get the action from app_xyz"""		
		if apps is None and self.fm:
			apps = self.fm.apps

		if apps is None:
			raise RuntimeError("AppContext has no source for applications!")

		app = apps.get(self.app)
		self.action = app(self)
		if isinstance(self.action, str):
			self.shell = True
			self.action = shell_escape(self.action)
		else:
			self.shell = False
	
	def run(self):
		"""
		Run the application in the way specified by the options.

		Returns False if nothing can be done, None if there was an error,
		otherwise the process object returned by Popen().

		This function tries to find an action if none is defined.
		"""

		# Try to find an action

		if self.action is None:
			self.get_action()

		if self.action is None:
			return False

		# Define some preconditions

		toggle_ui = True
		pipe_output = False

		self.squash_flags()

		kw = {}
		kw['stdout'] = sys.stdout
		kw['stderr'] = sys.stderr
		kw['args'] = self.action

		for word in ('shell', 'stdout', 'stdin', 'stderr'):
			if getattr(self, word) is not None:
				kw[word] = getattr(self, word)

		# Evaluate the flags to determine keywords
		# for Popen() and other variables

		if 's' in self.flags or 'd' in self.flags:
			kw['stdout'] = kw['stderr'] = kw['stdin'] = devnull

		if 'p' in self.flags:
			kw['stdout'] = PIPE
			kw['stderr'] = PIPE
			toggle_ui = False
			pipe_output = True
			self.wait = False

		if 'd' in self.flags:
			toggle_ui = False
			self.wait = False

		# Finally, run it

		if toggle_ui:
			self._activate_ui(False)

		try:
			process = None
			try:
				process = Popen(**kw)
			except:
				if self.fm:
					self.fm.notify("Failed to run: " + \
							' '.join(kw['args']), bad=True)
			else:
				if self.wait:
					waitpid_no_intr(process.pid)
		finally:
			if toggle_ui:
				self._activate_ui(True)
			
			if pipe_output and process:
				return run(app='pager', stdin=process.stdout, fm=self.fm)

			return process

	def _activate_ui(self, boolean):
		if self.fm and self.fm.ui:
			if boolean:
				self.fm.ui.initialize()
			else:
				self.fm.ui.suspend()

def run(action=None, **kw):
	"""Shortcut for creating and immediately running an AppContext."""
	app = AppContext(action=action, **kw)
	return app.run()

def tup(*args):
	"""
	This helper function creates a tuple out of the arguments.

	('a', ) + tuple(some_iterator)
	is equivalent to:
	tup('a', *some_iterator)
	"""
	return args

def depends_on(*args):
	args = tuple(flatten(args))
	def decorator(fnc):
		fnc.dependencies = args
		return fnc
	return decorator
