"""Help files are located here."""

from inspect import cleandoc

NO_TOPIC = """The help topic was not found."""

NO_HELP = """No help was found.

Possibly the program was invoked with "python -QQ" which
discards all documentation."""

HELP_TOPICS = ('index', 'movement')

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
