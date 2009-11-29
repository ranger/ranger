
TUPLE_KEYS = ['wdisplay', 'wstatusbar', 'wtitlebar', 'wconsole', 'folder', 'executable', 'media', 'link', 'broken', 'selected']

COLOR_PAIRS = {10: 0}

def get_color(fg, bg):
	import curses

	c = bg+2 + 9*(fg + 2)

	if c not in COLOR_PAIRS:
		size = len(COLOR_PAIRS)
		curses.init_pair(size, fg, bg)
		COLOR_PAIRS[c] = size

	return COLOR_PAIRS[c]


class ColorSchemeContext(object):
	def __init__(self, dictionary):
		object.__init__(self)

		self.__tuple__ = None
		for key in TUPLE_KEYS:
			if key in dictionary:
				self.__dict__[key] = dictionary[key]
			else:
				self.__dict__[key] = False

	def to_tuple(self):
		d = self.__dict__

		if '__tuple__' is None:
			self.__tuple__ = tuple(d[key] for key in TUPLE_KEYS)

		return self.__tuple__

class ColorScheme():
	def __init__(self):
		self.cache = {}

	def get(self, **keywords):
		con = ColorSchemeContext(keywords)
		tup = con.to_tuple()
		try:
			return self.cache[tup]
		except KeyError:
			color = self.use(con)
			self.cache[tup] = color
			return color
	
	def use(self, context):
		return -1, -1, 0
		
