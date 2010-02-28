# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
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

"""Help files are located here."""

from inspect import cleandoc

NO_TOPIC = """The help topic was not found."""

NO_HELP = """No help was found.

Possibly the program was invoked with "python -OO" which
discards all documentation."""

HELP_TOPICS = ('index', 'movement', 'starting', 'console', 'fileop')

def get_docstring_of_module(path, module_name):
	imported = __import__(path, fromlist=[module_name])
	return getattr(imported, module_name).__doc__

def get_help(topic):
	try:
		doc = get_docstring_of_module('ranger.help', topic)
	except (ImportError, AttributeError):
		return NO_TOPIC
	if isinstance(doc, str):
		return cleandoc(doc)
	return NO_HELP

def get_help_by_index(i):
	try:
		return get_help(HELP_TOPICS[i])
	except IndexError:
		return NO_TOPIC
