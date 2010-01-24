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
This module provides helper functions/classes for ranger.defaults.apps.
"""

import os, sys
from subprocess import Popen, PIPE
from ranger.ext.iter_tools import flatten
from ranger.shared import FileManagerAware


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

	def apply(self, app, context):
		if not app:
			app = 'default'
		try:
			handler = getattr(self, 'app_' + app)
		except AttributeError:
			handler = self.app_default
		return handler(context)

	def has(self, app):
		"""Returns whether an application is defined"""
		return hasattr(self, 'app_' + app)

	def all(self):
		"""Returns a list with all application functions"""
		methods = self.__class__.__dict__
		return [meth[4:] for meth in methods if meth.startswith('app_')]


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
