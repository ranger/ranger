class NotLoadedYet(Exception):
	pass

T_FILE = 'file'
T_DIRECTORY = 'directory'
T_UNKNOWN = 'unknown'
T_NONEXISTANT = 'nonexistant'

BAD_INFO = None

CONTAINER_EXTENSIONS = 'rar zip tar gz bz bz2 tgz 7z iso cab'.split()
DOCUMENT_EXTENSIONS = 'pdf doc ppt odt'.split()
DOCUMENT_BASENAMES = 'README TODO LICENSE'.split()

class FileSystemObject(object):

	def __init__(self, path):
		if type(self) == FileSystemObject:
			raise TypeError("FileSystemObject is an abstract class and cannot be initialized.")

		from os.path import basename, dirname

		self.path = path
		self.basename = basename(path)
		self.dirname = dirname(path)
		try:
			self.extension = self.basename[self.basename.rindex('.') + 1:]
		except ValueError:
			self.extension = None
		self.exists = False
		self.accessible = False
		self.marked = False
		self.tagged = False
		self.frozen = False
		self.loaded = False
		self.runnable = False
		self.islink = False
		self.brokenlink = False
		self.stat = None
		self.infostring = None
		self.permissions = None
		self.type = T_UNKNOWN

		self.set_mimetype()
	
	def __str__(self):
		return str(self.path)

	def set_mimetype(self):
		import ranger.mimetype as mimetype
		try:
			self.mimetype = mimetype.get() [self.extension]
		except KeyError:
			self.mimetype = ''

		self.video = self.mimetype.startswith('video')
		self.image = self.mimetype.startswith('image')
		self.audio = self.mimetype.startswith('audio')
		self.media = self.video or self.image or self.audio
		self.document = self.mimetype.startswith('text') or (self.extension in DOCUMENT_EXTENSIONS) or (self.basename in DOCUMENT_BASENAMES)
		self.container = self.extension in CONTAINER_EXTENSIONS

		keys = ('video', 'audio', 'image', 'media', 'document', 'container')
		self.mimetype_tuple = tuple(key for key in keys if getattr(self, key))

		if self.mimetype == '':
			self.mimetype = None

	# load() reads useful information about the file from the file system
	# and caches it in instance attributes.
	def load(self):
		import os
		from ranger.helper import human_readable

		self.loaded = True

		if os.access(self.path, os.F_OK):
			self.stat = os.stat(self.path)
			self.islink = os.path.islink(self.path)
			self.exists = True
			self.accessible = True

			if os.path.isdir(self.path):
				self.type = T_DIRECTORY
				try:
					self.size = len(os.listdir(self.path))
					self.infostring = ' %d' % self.size
					self.runnable = True
				except OSError:
					self.infostring = BAD_INFO
					self.runnable = False
					self.accessible = False
			elif os.path.isfile(self.path):
				self.type = T_FILE
				self.size = self.stat.st_size
				self.infostring = ' ' + human_readable(self.stat.st_size)
			else:
				self.type = T_UNKNOWN
				self.infostring = None

		else:
			self.stat = None
			self.islink = False
			self.infostring = None
			self.type = T_NONEXISTANT
			self.exists = False
			self.runnable = False
			self.accessible = False

	def load_once(self):
		if not self.loaded:
			self.load()
			return True
		return False

	def load_if_outdated(self):
		if self.load_once(): return True

		import os
		real_mtime = os.stat(self.path).st_mtime
		cached_mtime = self.stat.st_mtime

		if real_mtime != cached_mtime:
			self.load()
			return True
		return False
