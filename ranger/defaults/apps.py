# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
# This configuration file is licensed under the same terms as ranger.
# ===================================================================
# This is the configuration file for file type detection and application
# handling.  It's all in python; lines beginning with # are comments.
#
# You can customize this in the file ~/.config/ranger/apps.py.
# It has the same syntax as this file.  In fact, you can just copy this
# file there with `ranger --copy-config=apps' and make your modifications.
# But make sure you update your configs when you update ranger.
#
# In order to add application definitions "on top of" the default ones
# in your ~/.config/ranger/apps.py, you should subclass the class defined
# here like this:
#
#   from ranger.defaults.apps import CustomApplications as DefaultApps
#   class CustomApplications(DeafultApps):
#       <your definitions here>
#
# To override app_defaults, you can write something like:
#
#       def app_defaults(self, c):
#           f = c.file
#           if f.extension == 'lol':
#               return "lolopener", c
#           return DefaultApps.app_default(self, c)
#
# ===================================================================
# This system is based on things called MODES and FLAGS.  You can read
# in the man page about them.  To remind you, here's a list of all flags.
# An uppercase flag inverts previous flags of the same name.
#     s   Silent mode.  Output will be discarded.
#     d   Detach the process.  (Run in background)
#     p   Redirect output to the pager
#     w   Wait for an Enter-press when the process is done
#     c   Run the current file only, instead of the selection
#     r   Run application with root privilege 
#     t   Run application in a new terminal window
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
#
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
#
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
#
# 4. "None" to indicate that no action was found.
#     return None
#
# ===================================================================
# When using the "either" method, ranger determines which program to
# pick by looking at its dependencies.  You can set dependencies by
# adding the decorator "depends_on":
#     @depends_on("vim")
#     def app_vim(self, context):
#         ....
# There is a special keyword which you can use as a dependence: "X"
# This ensures that the program will only run when X is running.
# ===================================================================

import ranger
from ranger.api.apps import *
from ranger.ext.get_executables import get_executables

class CustomApplications(Applications):
	def app_default(self, c):
		"""How to determine the default application?"""
		f = c.file

		if f.basename.lower() == 'makefile' and c.mode == 1:
			made = self.either(c, 'make')
			if made: return made

		if f.extension is not None:
			if f.extension in ('pdf', ):
				return self.either(c, 'llpp', 'zathura', 'mupdf', 'apvlv',
						'evince', 'okular', 'epdfview')
			if f.extension == 'djvu':
				return self.either(c, 'evince')
			if f.extension in ('xml', 'csv'):
				return self.either(c, 'editor')
			if f.extension == 'mid':
				return self.either(c, 'wildmidi')
			if f.extension in ('html', 'htm', 'xhtml') or f.extension == 'swf':
				c.flags += 'd'
				handler = self.either(c,
						'luakit', 'uzbl', 'vimprobable', 'vimprobable2', 'jumanji',
						'firefox', 'seamonkey', 'iceweasel', 'opera',
						'surf', 'midori', 'epiphany', 'konqueror')
				# Only return if some program was found:
				if handler:
					return handler
			if f.extension in ('html', 'htm', 'xhtml'):
				# These browsers can't handle flash, so they're not called above.
				c.flags += 'D'
				return self.either(c, 'elinks', 'links', 'links2', 'lynx', 'w3m')
			if f.extension == 'nes':
				return self.either(c, 'fceux')
			if f.extension in ('swc', 'smc', 'sfc'):
				return self.either(c, 'zsnes')
			if f.extension == 'doc':
				return self.either(c, 'abiword', 'libreoffice',
						'soffice', 'ooffice')
			if f.extension in ('odt', 'ods', 'odp', 'odf', 'odg', 'sxc',
					'stc', 'xls', 'xlsx', 'xlt', 'xlw', 'gnm', 'gnumeric'):
				return self.either(c, 'gnumeric', 'kspread',
						'libreoffice', 'soffice', 'ooffice')

		if f.mimetype is not None:
			if INTERPRETED_LANGUAGES.match(f.mimetype):
				return self.either(c, 'edit_or_run')

		if f.container:
			return self.either(c, 'aunpack', 'file_roller')

		if f.video or f.audio:
			if f.video:
				c.flags += 'd'
			return self.either(c, 'smplayer', 'gmplayer', 'mplayer2',
					'mplayer', 'vlc', 'totem')

		if f.image:
			if c.mode in (11, 12, 13, 14):
				return self.either(c, 'set_bg_with_feh')
			else:
				return self.either(c, 'sxiv', 'feh', 'eog', 'mirage')

		if f.document or f.filetype.startswith('text') or f.size == 0:
			return self.either(c, 'editor')

		# You can put this at the top of the function and mimeopen will
		# always be used for every file.
		return self.either(c, 'mimeopen')


	# ----------------------------------------- application definitions
	# Note: Trivial application definitions are at the bottom
	def app_pager(self, c):
		return 'less', '-R', c

	def app_editor(self, c):
		try:
			default_editor = os.environ['EDITOR']
		except KeyError:
			pass
		else:
			parts = default_editor.split()
			exe_name = os.path.basename(parts[0])
			if exe_name in get_executables():
				return tuple(parts) + tuple(c)

		return self.either(c, 'vim', 'emacs', 'nano')

	def app_edit_or_run(self, c):
		if c.mode is 1:
			return self.app_self(c)
		return self.app_editor(c)

	@depends_on('mplayer')
	def app_mplayer(self, c):
		if c.mode is 1:
			return 'mplayer', '-fs', c

		elif c.mode is 2:
			args = "mplayer -fs -sid 0 -vfm ffmpeg -lavdopts " \
					"lowres=1:fast:skiploopfilter=all:threads=8".split()
			args.extend(c)
			return args

		elif c.mode is 3:
			return 'mplayer', '-mixer', 'software', c

		else:
			return 'mplayer', c

	@depends_on('mplayer2')
	def app_mplayer2(self, c):
		args = list(self.app_mplayer(c))
		args[0] += '2'
		return args

	# A dependence on "X" means: this programs requires a running X server!
	@depends_on('feh', 'X')
	def app_set_bg_with_feh(self, c):
		c.flags += 'd'
		arg = {11: '--bg-scale', 12: '--bg-tile', 13: '--bg-center',
				14: '--bg-fill'}
		if c.mode in arg:
			return 'feh', arg[c.mode], c.file.path
		return 'feh', arg[11], c.file.path

	@depends_on('feh', 'X')
	def app_feh(self, c):
		c.flags += 'd'
		if c.mode is 0 and len(c.files) is 1 and self.fm.env.cwd:
			# view all files in the cwd
			images = [f.basename for f in self.fm.env.cwd.files if f.image]
			return 'feh', '--start-at', c.file.basename, images
		return 'feh', c

	@depends_on('sxiv', 'X')
	def app_sxiv(self, c):
		c.flags = 'd' + c.flags
		if len(c.files) is 1 and self.fm.env.cwd:
			images = [f.basename for f in self.fm.env.cwd.files if f.image]
			try:
				position = images.index(c.file.basename) + 1
			except:
				return None
			return 'sxiv', '-n', str(position), images
		return 'sxiv', c

	@depends_on('aunpack')
	def app_aunpack(self, c):
		if c.mode is 0:
			c.flags += 'p'
			return 'aunpack', '-l', c.file.path
		return 'aunpack', c.file.path

	@depends_on('file-roller', 'X')
	def app_file_roller(self, c):
		c.flags += 'd'
		return 'file-roller', c.file.path

	@depends_on('make')
	def app_make(self, c):
		if c.mode is 0:
			return "make"
		if c.mode is 1:
			return "make", "install"
		if c.mode is 2:
			return "make", "clear"

	@depends_on('java')
	def app_java(self, c):
		def strip_extensions(file):
			if '.' in file.basename:
				return file.path[:file.path.index('.')]
			return file.path
		files_without_extensions = map(strip_extensions, c.files)
		return "java", files_without_extensions

	@depends_on('totem', 'X')
	def app_totem(self, c):
		if c.mode is 0:
			return "totem", c
		if c.mode is 1:
			return "totem", "--fullscreen", c

	@depends_on('mimeopen')
	def app_mimeopen(self, c):
		if c.mode is 0:
			return "mimeopen", c
		if c.mode is 1: 
			# Will ask user to select program
			# aka "Open with..."
			return "mimeopen", "--ask", c


# Often a programs invocation is trivial.  For example:
#    vim test.py readme.txt [...]
#
# This could be implemented like:
#    @depends_on("vim")
#    def app_vim(self, context):
#        return "vim", context
#
# But this is redundant and ranger does this automatically.  However, sometimes
# you want to change some properties like flags or dependencies.
# The method "generic" defines a generic method for the given programs which
# looks like the one above, but you can add dependencies and flags here.
# Add programs (that are not defined yet) here if they should only run in X:
CustomApplications.generic('fceux', 'wine', 'zsnes', deps=['X'])

# Add those which should only run in X AND should be detached/forked here:
CustomApplications.generic(
	'luakit', 'uzbl', 'vimprobable', 'vimprobable2', 'jumanji',
	'firefox', 'seamonkey', 'iceweasel', 'opera',
	'surf', 'midori', 'epiphany', 'konqueror',
	'evince', 'zathura', 'apvlv', 'okular', 'epdfview', 'mupdf', 'llpp',
	'eog', 'mirage', 'gimp',
	'libreoffice', 'soffice', 'ooffice', 'gnumeric', 'kspread', 'abiword',
	'gmplayer', 'smplayer', 'vlc',
			flags='d', deps=['X'])

# What filetypes are recognized as scripts for interpreted languages?
# This regular expression is used in app_default()
INTERPRETED_LANGUAGES = re.compile(r'''
	^(text|application)/x-(
		haskell|perl|python|ruby|sh
	)$''', re.VERBOSE)
