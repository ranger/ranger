import os, sys
from ranger.ext.waitpid_no_intr import waitpid_no_intr
from subprocess import Popen, PIPE

devnull = open(os.devnull, 'a')

ALLOWED_FLAGS = 'sdpSDP'

class Applications(object):
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
	arguments.
	It has one argument, which is the AppContext instance.

	You should define app_default, app_pager and app_editor since
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
		self.shell = isinstance(self.action, str)
	
	def run(self):
		"""
		Run the application in the way specified by the options.

		Returns False if nothing can be done, None if there was an error,
		otherwise the process object returned by Popen().

		This function tries to find an action if none is defined.
		"""

		self.squash_flags()
		if self.action is None:
			self.get_action()

		# ---------------------------- determine keywords for Popen()

		kw = {}
		kw['stdout'] = sys.stderr
		kw['stderr'] = sys.stderr
		kw['args'] = self.action

		if kw['args'] is None:
			return False

		for word in ('shell', 'stdout', 'stdin', 'stderr'):
			if getattr(self, word) is not None:
				kw[word] = getattr(self, word)

		if 's' in self.flags or 'd' in self.flags:
			kw['stdout'] = kw['stderr'] = kw['stdin'] = devnull

		# --------------------------- run them
		toggle_ui = True
		pipe_output = False
		process = None

		if 'p' in self.flags:
			kw['stdout'] = PIPE
			kw['stderr'] = PIPE
			toggle_ui = False
			pipe_output = True
			self.wait = False

		if 'd' in self.flags:
			toggle_ui = False
			self.wait = False

		if toggle_ui:
			self._activate_ui(False)

		try:
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
	return tuple(args)
