# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This module is an abstract layer over subprocess.Popen

It gives you highlevel control about how processes are run.

Example:
run = Runner(logfunc=print)
run('sleep 2', wait=True)         # waits until the process exists
run(['ls', '--help'], flags='p')  # pipes output to pager
run()                             # prints an error message

List of allowed flags:
s: silent mode. output will be discarded.
d: detach the process.
p: redirect output to the pager
c: run only the current file (not handled here)
w: wait for enter-press afterwards
r: run application with root privilege (requires sudo)
t: run application in a new terminal window
(An uppercase key negates the respective lower case flag)
"""

import os
import sys
from subprocess import Popen, PIPE
from ranger.ext.get_executables import get_executables


ALLOWED_FLAGS = 'sdpwcrtSDPWCRT'


def press_enter():
	"""Wait for an ENTER-press"""
	sys.stdout.write("Press ENTER to continue")
	try:
		waitfnc = raw_input
	except NameError:
		# "raw_input" not available in python3
		waitfnc = input
	waitfnc()


class Context(object):
	"""
	A context object contains data on how to run a process.

	The attributes are:
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
	popen_kws -- keyword arguments which are directly passed to Popen
	"""

	def __init__(self, **keywords):
		self.__dict__ = keywords

	@property
	def filepaths(self):
		try:
			return [f.path for f in self.files]
		except:
			return []

	def __iter__(self):
		"""Iterate over file paths"""
		for item in self.filepaths:
			yield item

	def squash_flags(self):
		"""Remove duplicates and lowercase counterparts of uppercase flags"""
		for flag in self.flags:
			if ord(flag) <= 90:
				bad = flag + flag.lower()
				self.flags = ''.join(c for c in self.flags if c not in bad)


class Runner(object):
	def __init__(self, ui=None, logfunc=None, apps=None, fm=None):
		self.ui = ui
		self.fm = fm
		self.logfunc = logfunc
		self.apps = apps
		self.zombies = set()

	def _log(self, text):
		try:
			self.logfunc(text)
		except TypeError:
			pass
		return False

	def _activate_ui(self, boolean):
		if self.ui is not None:
			if boolean:
				try: self.ui.initialize()
				except: self._log("Failed to initialize UI")
			else:
				try: self.ui.suspend()
				except: self._log("Failed to suspend UI")

	def __call__(self, action=None, try_app_first=False,
			app='default', files=None, mode=0,
			flags='', wait=True, **popen_kws):
		"""
		Run the application in the way specified by the options.

		Returns False if nothing can be done, None if there was an error,
		otherwise the process object returned by Popen().

		This function tries to find an action if none is defined.
		"""

		# Find an action if none was supplied by
		# creating a Context object and passing it to
		# an Application object.

		context = Context(app=app, files=files, mode=mode, fm=self.fm,
				flags=flags, wait=wait, popen_kws=popen_kws,
				file=files and files[0] or None)

		if self.apps:
			if try_app_first and action is not None:
				test = self.apps.apply(app, context)
				if test:
					action = test
			if action is None:
				action = self.apps.apply(app, context)
				if action is None:
					return self._log("No action found!")

		if action is None:
			return self._log("No way of determining the action!")

		# Preconditions

		context.squash_flags()
		popen_kws = context.popen_kws  # shortcut

		toggle_ui = True
		pipe_output = False
		wait_for_enter = False
		devnull = None

		if 'shell' not in popen_kws:
			popen_kws['shell'] = isinstance(action, str)
		if 'stdout' not in popen_kws:
			popen_kws['stdout'] = sys.stdout
		if 'stderr' not in popen_kws:
			popen_kws['stderr'] = sys.stderr

		# Evaluate the flags to determine keywords
		# for Popen() and other variables

		if 'p' in context.flags:
			popen_kws['stdout'] = PIPE
			popen_kws['stderr'] = PIPE
			toggle_ui = False
			pipe_output = True
			context.wait = False
		if 's' in context.flags or 'd' in context.flags:
			devnull_writable = open(os.devnull, 'w')
			devnull_readable = open(os.devnull, 'r')
			for key in ('stdout', 'stderr'):
				popen_kws[key] = devnull_writable
			popen_kws['stdin'] = devnull_readable
		if 'd' in context.flags:
			toggle_ui = False
			context.wait = False
		if 'w' in context.flags:
			if not pipe_output and context.wait: # <-- sanity check
				wait_for_enter = True
		if 'r' in context.flags:
			if 'sudo' not in get_executables():
				return self._log("Can not run with 'r' flag, sudo is not installed!")
			dflag = ('d' in context.flags)
			if isinstance(action, str):
				action = 'sudo ' + (dflag and '-b ' or '') + action
			else:
				action = ['sudo'] + (dflag and ['-b'] or []) + action
			toggle_ui = True
			context.wait = True
		if 't' in context.flags:
			if 'DISPLAY' not in os.environ:
				return self._log("Can not run with 't' flag, no display found!")
			term = os.environ.get('TERMCMD', os.environ.get('TERM'))
			if term not in get_executables():
				term = 'x-terminal-emulator'
			if term not in get_executables():
				term = 'xterm'
			if isinstance(action, str):
				action = term + ' -e ' + action
			else:
				action = [term, '-e'] + action
			toggle_ui = False
			context.wait = False

		popen_kws['args'] = action
		# Finally, run it

		if toggle_ui:
			self._activate_ui(False)
		try:
			error = None
			process = None
			self.fm.signal_emit('runner.execute.before',
					popen_kws=popen_kws, context=context)
			try:
				process = Popen(**popen_kws)
			except Exception as e:
				error = e
				self._log("Failed to run: %s\n%s" % (str(action), str(e)))
			else:
				if context.wait:
					process.wait()
				else:
					self.zombies.add(process)
				if wait_for_enter:
					press_enter()
		finally:
			self.fm.signal_emit('runner.execute.after',
					popen_kws=popen_kws, context=context, error=error)
			if devnull:
				devnull.close()
			if toggle_ui:
				self._activate_ui(True)
			if pipe_output and process:
				return self(action='less', app='pager', try_app_first=True,
						stdin=process.stdout)
			return process
