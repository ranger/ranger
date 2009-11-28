#import curses

color_pairs = {10: 0}


#class ColorScheme():
#	def isdir


#def get_color(fg, bg):
#	c = bg+2 + 9*(fg + 2)
#	try:
#		return color_pairs[c]
#	except KeyError:
#		size = len(color_pairs)
#		curses.init_pair(size, curses.COLOR_RED, curses.COLOR_WHITE)
#		color_pairs[c] = size
#		return color_pairs[c]
#
#def color(fg = -1, bg = -1, attribute = 0):
#	pass
##	prin
#	curses.attrset(attribute | curses.color_pair(get_color(fg, bg)))

#color(-1, -1)
#print(color_pairs)
