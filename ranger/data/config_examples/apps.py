# ===================================================================
# This is the configuration file for filetype detection and application
# handling.  It's all in python; lines beginning with # are comments.
#
# Here, the class "CustomApplications" is defined as a subclass of the default
# application handler class.  It is located at ranger/defaults/apps.py and
# contains a whole lot of definitions.  You can just copy & paste them here.
# ===================================================================

# Import the basics
from ranger.defaults.apps import CustomApplications as DefaultApps
from ranger.api.apps import *

# By default, we do nothing.
class CustomApplications(DefaultApps):
	pass

#	def app_kaffeine(self, context):
#		return 'kaffeine', context
#
#	def app_feh_fullscreen_by_default(self, context):
#		return 'feh', '-F', context
#
#	def app_default(self, context):
#		f = context.file #shortcut
#		if f.video or f.audio:
#			return self.app_kaffeine(context)
#
#		if f.image and context.mode == 0:
#			return self.app_feh_fullscreen_by_default(context)
#
#		return DefaultApps.app_default(self, context)
