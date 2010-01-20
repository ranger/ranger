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

from re import compile, VERBOSE
from ranger.applications import *

INTERPRETED_LANGUAGES = compile(r'''
	^(text|application)\/x-(
		haskell|perl|python|ruby|sh
	)$''', VERBOSE)

class CustomApplications(Applications):
	def app_default(self, c):
		"""How to determine the default application?"""
		f = c.file

		if f.extension is not None:
			if f.extension in ('pdf'):
				return self.app_apvlv(c)
			if f.extension in ('swc', 'smc'):
				return self.app_zsnes(c)

		if INTERPRETED_LANGUAGES.match(f.mimetype):
			return self.app_edit_or_run(c)

		if f.container:
			return self.app_aunpack(c)

		if f.video or f.audio:
			if f.video:
				c.flags += 'd'
			return self.app_mplayer(c)
		
		if f.image:
			return self.app_feh(c)

		if f.document:
			return self.app_editor(c)

	# ----------------------------------------- application definitions
	def app_pager(self, c):
		return tup('less', *c)

	def app_vim(self, c):
		return tup('vim', *c)

	app_editor = app_vim

	def app_edit_or_run(self, c):
		if c.mode is 1:
			return self.app_self(c)
		return self.app_editor(c)

	def app_mplayer(self, c):
		if c.mode is 1:
			return tup('mplayer', *c)

		elif c.mode is 2:
			args = "mplayer -fs -sid 0 -vfm ffmpeg -lavdopts" \
					"lowres=1:fast:skiploopfilter=all:threads=8".split()
			args.extend(c)
			return tup(*args)

		elif c.mode is 3:
			return tup('mplayer', '-mixer', 'software', *c)

		else:
			return tup('mplayer', '-fs', *c)

	def app_feh(self, c):
		arg = {1: '--bg-scale', 2: '--bg-tile', 3: '--bg-center'}

		c.flags += 'd'

		if c.mode in arg:
			return tup('feh', arg[c.mode], c.file.path)
		if c.mode is 4:
			return tup('gimp', *c)
		return tup('feh', *c)

	def app_aunpack(self, c):
		if c.mode is 0:
			c.flags += 'p'
			return tup('aunpack', '-l', c.file.path)
		return tup('aunpack', c.file.path)
	
	def app_apvlv(self, c):
		c.flags += 'd'
		return tup('apvlv', *c)

	def app_make(self, c):
		if c.mode is 0:
			return tup("make")
		if c.mode is 1:
			return tup("make", "install")
		if c.mode is 2:
			return tup("make", "clear")
	
	def app_firefox(self, c):
		return tup("firefox")

	def app_javac(self, c):
		return tup("javac", *c)
	
	def app_java(self, c):
		def strip_extensions(file):
			if '.' in file.basename:
				return file.path[:file.path.index('.')]
			return file.path
		files_without_extensions = map(strip_extensions, c.files)
		return tup("java", files_without_extensions)
	
	def app_zsnes(self, c):
		return tup("zsnes", c.file)
	
	def app_evince(self, c):
		return tup("evince", *c)
	
	def app_wine(self, c):
		return tup("wine", c.file)

	def app_totem(self, c):
		if c.mode is 0:
			return tup("totem", "--fullscreen", *c)
		if c.mode is 1:
			return tup("totem", *c)
