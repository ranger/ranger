CONTAINER_EXTENSIONS = 'rar zip tar gz bz bz2 tgz 7z iso cab'.split()
DOCUMENT_EXTENSIONS = 'pdf doc ppt odt'.split()
DOCUMENT_BASENAMES = 'README TODO LICENSE'.split()

from . import T_FILE, T_DIRECTORY, T_UNKNOWN, T_NONEXISTANT, BAD_INFO
from ranger.shared import MimeTypeAware, FileManagerAware
class FileSystemObject(MimeTypeAware, FileManagerAware):
	path = None
	basename = None
	dirname = None
	extension = None
	exists = False
	accessible = False
	marked = False
	tagged = False
	frozen = False
	loaded = False
	runnable = False
	islink = False
	brokenlink = False
	stat = None
	infostring = None
	permissions = None
	type = T_UNKNOWN

	last_used = None

	video = False
	image = False
	audio = False
	media = False
	document = False
	container = False
	mimetype_tuple = ()

	def __init__(self, path):
		MimeTypeAware.__init__(self)
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

		self.set_mimetype()
		self.use()
	
	def __str__(self):
		"""returns a string containing the absolute path"""
		return str(self.path)

	def use(self):
		"""mark the filesystem-object as used at the current time"""
		import time
		self.last_used = time.time()
	
	def is_older_than(self, seconds):
		"""returns whether this object wasn't use()d in the last n seconds"""
		import time
		return self.last_used + seconds < time.time()
	
	def set_mimetype(self):
		"""assign attributes such as self.video according to the mimetype"""
		try:
			self.mimetype = self.mimetypes[self.extension]
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

	def load(self):
		"""reads useful information about the filesystem-object from the filesystem
and caches it for later use"""
		import os
		from ranger.ext.human_readable import human_readable

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
		"""calls load() if it has not been called at least once yet"""
		if not self.loaded:
			self.load()
			return True
		return False

	def go(self):
		"""enter the directory if the filemanager is running"""
		if self.fm:
			return self.fm.enter_dir(self.path)
		return False

	def load_if_outdated(self):
		"""calls load() if the currently cached information is outdated or nonexistant"""
		if self.load_once(): return True

		import os
		real_mtime = os.stat(self.path).st_mtime
		cached_mtime = self.stat.st_mtime

		if real_mtime != cached_mtime:
			self.load()
			return True
		return False
