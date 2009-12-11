#!/usr/bin/python3
"""Generate pydoc documentation and move it to the doc directory.
THIS WILL DELETE ALL EXISTING HTML FILES IN THAT DIRECTORY, so don't
store important content there."""

import pydoc, os, sys
if __name__ == '__main__':
	docdir = 'doc'
	os.chdir(sys.path[0])
	try: os.mkdir(docdir)
	except: pass


	for fname in os.listdir(docdir):
		if fname.endswith('.html'):
			os.remove(os.path.join(docdir, fname))

	pydoc.writedocs('.')
	pydoc.writedoc('curses')
	pydoc.writedoc('curses.ascii')
	pydoc.writedoc('os')
	pydoc.writedoc('os.path')
	pydoc.writedoc('sys')

	for fname in os.listdir('.'):
		if fname.endswith('.html'):
			os.rename(fname, os.path.join(docdir, fname))

