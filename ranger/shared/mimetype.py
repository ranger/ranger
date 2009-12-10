from ranger import relpath
class MimeTypeAware(object):
	mimetypes = {}
	__initialized = False
	def __init__(self):
		if not MimeTypeAware.__initialized:
			MimeTypeAware.__initialized = True
			import os, sys, pickle
			MimeTypeAware.mimetypes.clear()

			f = open(relpath('data/mime.dat'), 'rb')
			MimeTypeAware.mimetypes.update(pickle.load(f))
			f.close()
