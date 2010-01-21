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

"""Help files are located here."""

from inspect import cleandoc

NO_TOPIC = """The help topic was not found."""

NO_HELP = """No help was found.

Possibly the program was invoked with "python -OO" which
discards all documentation."""

HELP_TOPICS = ('index', 'movement', 'starting')

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
