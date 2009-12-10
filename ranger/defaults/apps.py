from ranger.applications import Applications, run

class CustomApplications(Applications):
	# How to determine the default application? {{{
	def app_default(self, **kw):
		f = kw['mainfile']

		if f.extension is not None and f.extension in ('pdf'):
			return self.app_evince(**kw)

		if f.container:
			return self.app_aunpack(**kw)

		if f.video or f.audio:
			if f.video:
				kw['flags'] += 'd'
			return self.app_mplayer(**kw)
		
		if f.image:
			return self.app_feh(**kw)

		if f.document:
			return self.app_editor(**kw)
	# }}}

	def app_pager(self, **kw):
		return run('less', *kw['files'], **kw)

	def app_vim(self, **kw):
		return run('vim', *kw['files'], **kw)

	app_editor = app_vim

	def app_mplayer(self, **kw):
		if kw['mode'] == 1:
			return run('mplayer', *kw['files'], **kw)

		elif kw['mode'] == 2:
			return run('mplayer', '-fs',
					'-sid', '0',
					'-vfm', 'ffmpeg',
					'-lavdopts', 'lowres=1:fast:skiploopfilter=all:threads=8',
					*kw['files'], **kw)

		elif kw['mode'] == 3:
			return run('mplayer',
					'-mixer', 'software',
					*kw['files'], **kw)

		else:
			return run('mplayer', '-fs', *kw['files'], **kw)

	def app_feh(self, **kw):
		if kw['files']:
			if kw['mode'] == 1:
				return run('feh', '--bg-scale', kw['files'][0], **kw)
			if kw['mode'] == 2:
				return run('feh', '--bg-tile', kw['files'][0], **kw)
			if kw['mode'] == 3:
				return run('feh', '--bg-center', kw['files'][0], **kw)
			if kw['mode'] == 4:
				return run('gimp', *kw['files'], **kw)
		return run('feh', *kw['files'], **kw)

	def app_aunpack(self, **kw):
		m = kw['mode']
		if m == 0:
			kw['flags'] += 'p'
			return run('aunpack', '-l', *kw['files'], **kw)
		elif m == 1:
			return run('aunpack', *kw['files'], **kw)
	
	def app_evince(self, **kw):
		return run('evince', *kw['files'], **kw)
