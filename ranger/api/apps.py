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

import os, sys, re
from ranger.api import *
from ranger.ext.iter_tools import flatten
from ranger.ext.get_executables import get_executables
from ranger.core.runner import Context
from ranger.core.shared import FileManagerAware


class Applications(FileManagerAware):
	"""
	This class contains definitions on how to run programs and should
	be extended in ranger.apps

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
		return 'less', context

	def app_editor(self, context):
		return ('vim', context)
	"""

	def _meets_dependencies(self, fnc):
		try:
			deps = fnc.dependencies
		except AttributeError:
			return True

		for dep in deps:
			if dep == 'X':
				if 'DISPLAY' not in os.environ or not os.environ['DISPLAY']:
					return False
				continue
			if hasattr(dep, 'dependencies') \
			and not self._meets_dependencies(dep):
				return False
			if dep not in get_executables():
				return False

		return True

	def either(self, context, *args):
		for app in args:
			try:
				application_handler = getattr(self, 'app_' + app)
			except AttributeError:
				if app in get_executables():
					return _generic_app(app, context)
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
			if app in get_executables():
				return [app] + list(context)
			handler = self.app_default
		arguments = handler(context)
		# flatten
		if isinstance(arguments, str):
			return arguments
		if arguments is None:
			return None
		result = []
		for obj in arguments:
			if isinstance(obj, (tuple, list, Context)):
				result.extend(obj)
			else:
				result.append(obj)
		return result

	def has(self, app):
		"""Returns whether an application is defined"""
		return hasattr(self, 'app_' + app)

	def all(self):
		"""Returns a list with all application functions"""
		result = set()
		# go through all the classes in the mro (method resolution order)
		# so subclasses will return the apps of their superclasses.
		for cls in self.__class__.__mro__:
			result |= set(m[4:] for m in cls.__dict__ if m.startswith('app_'))
		return sorted(result)

	@classmethod
	def generic(cls, *args, **keywords):
		flags = 'flags' in keywords and keywords['flags'] or ""
		deps = 'deps' in keywords and keywords['deps'] or ()
		for name in args:
			assert isinstance(name, str)
			if not hasattr(cls, "app_" + name):
				fnc = _generic_wrapper(name, flags=flags)
				fnc = depends_on(*deps)(fnc)
				setattr(cls, "app_" + name, fnc)


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
		try:
			fnc.dependencies += args
		except:
			fnc.dependencies  = args
		return fnc
	return decorator


def _generic_app(name, context, flags=''):
	"""Use this function when no other information is given"""
	context.flags += flags
	return name, context


def _generic_wrapper(name, flags=''):
	"""Wraps _generic_app into a method for Applications"""
	assert isinstance(name, str)
	return depends_on(name)(lambda self, context:
			_generic_app(name, context, flags))
