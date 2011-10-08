# ===================================================================
# This is the configuration file for file type detection and application
# handling.  It's all in python; lines beginning with # are comments.
#
# Scroll down for a few examples.
# ===================================================================
# This system is based on things called MODES and FLAGS.  You can read
# in the man page about them.  To remind you, here's a list of all flags.
# An uppercase flag inverts previous flags of the same name.
#     s   Silent mode.  Output will be discarded.
#     d   Detach the process.  (Run in background)
#     p   Redirect output to the pager
#     w   Wait for an Enter-press when the process is done
#     c   Run the current file only, instead of the selection
#
# To implement flags in this file, you could do this:
#     context.flags += "d"
# Another example:
#     context.flags += "Dw"
#
# To implement modes in this file, you can do something like:
#     if context.mode == 1:
#         <run in one way>
#     elif context.mode == 2:
#         <run in another way>
# ===================================================================
# The methods are called with a "context" object which provides some
# attributes that transfer information.  Relevant attributes are:
#
# mode -- a number, mainly used in determining the action in app_xyz()
# flags -- a string with flags which change the way programs are run
# files -- a list containing files, mainly used in app_xyz
# filepaths -- a list of the paths of each file
# file -- an arbitrary file from that list (or None)
# fm -- the filemanager instance
# popen_kws -- keyword arguments which are directly passed to Popen
# ===================================================================
# The return value of the functions should be either:
# 1. A reference to another app, like:
#     return self.app_editor(context)
#
# 2. A call to the "either" method, which uses the first program that
# is installed on your system.  If none are installed, None is returned.
#     return self.either(context, "libreoffice", "soffice", "ooffice")
#
# 3. A tuple of arguments that should be run.
#     return "mplayer", "-fs", context.file.path
# If you use lists instead of strings, they will be flattened:
#     args = ["-fs", "-shuf"]
#     return "mplayer", args, context.filepaths
# "context.filepaths" can, and will often be abbreviated with just "context":
#     return "mplayer", context
# ===================================================================

# Import the basics
from ranger.defaults.apps import CustomApplications as DefaultApps
from ranger.api.apps import *

#
# Here, the class "CustomApplications" is defined as a subclass of the default
# application handler class.  It is located at ranger/defaults/apps.py and
# contains a whole lot of definitions.  The reason why we don't put them here
# is that when you update, this file doesn't change.
class CustomApplications(DefaultApps):
	# By default, this just inherits all methods from DefaultApps
	pass

#	def app_kaffeine(self, context):
#		return 'kaffeine', context
#
#	def app_feh_fullscreen_by_default(self, context):
#		return 'feh', '-F', context
#
#	# app_default is the function that is always called to determine which
#	# application to run, unless you specify one manually with :open_with
#	def app_default(self, context):
#		f = context.file #shortcut
#		if f.video or f.audio:
#			return self.app_kaffeine(context)
#
#		if f.image and context.mode == 0:
#			return self.app_feh_fullscreen_by_default(context)
#
#		return DefaultApps.app_default(self, context)
#
#	# You could write this to use an entirely different program to open files:
#	def app_default(self, context):
#		return "mimeopen", context


## Often a programs invocation is trivial.  For example:
##    vim test.py readme.txt [...]
## This could be implemented like:
##    @depends_on("vim")
##    def app_vim(self, context):
##        return "vim", context
## Instead of creating such a generic function for each program, just add
## its name here and it will be automatically done for you.
#CustomApplications.generic('zsnes', 'javac')

## By setting flags='d', this programs will not block ranger's terminal:
#CustomApplications.generic('gimp', 'evince', flags='d')
