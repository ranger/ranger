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

import stat
import os
from os.path import isfile, join, exists
from ranger.ext.iter_tools import unique

def get_executables(*paths):
	"""
	Return all executable files in each of the given directories.

	Looks in $PATH by default.
	"""
	if not paths:
		try:
			pathstring = os.environ['PATH']
		except KeyError:
			return ()
		paths = unique(pathstring.split(':'))

	executables = set()
	for path in paths:
		try:
			content = os.listdir(path)
		except:
			continue
		for item in content:
			abspath = join(path, item)
			try:
				filestat = os.stat(abspath)
			except:
				continue
			if filestat.st_mode & (stat.S_IXOTH | stat.S_IFREG):
				executables.add(item)
	return executables
