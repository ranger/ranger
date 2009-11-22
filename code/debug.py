# a module to faciliate debuggin

LOGFILE = '/tmp/errorlog'

def log(txt):
	f = open(LOGFILE, 'a')
	f.write("r1: ")
	f.write(str(txt))
	f.write("\n")
	f.close()


