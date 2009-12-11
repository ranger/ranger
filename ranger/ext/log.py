LOGFILE = '/tmp/errorlog'

def log(*objects, **keywords):
	"""Writes objects to a logfile.
Has the same arguments as print() in python3"""
	start = 'start' in keywords and keywords['start'] or 'ranger:'
	sep   =   'sep' in keywords and keywords['sep']   or ' '
	_file =  'file' in keywords and keywords['file']  or open(LOGFILE, 'a')
	end   =   'end' in keywords and keywords['end']   or '\n'
	_file.write(sep.join((start, ) + objects) + end)
	
#for python3-only versions, this could be replaced with:
#
#def log(*objects, start='ranger:', sep=' ', end='\n'):
#	print(start, *objects, end=end, sep=sep, file=open(LOGFILE, 'a'))
