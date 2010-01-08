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

"""Colorschemes are required to be located here,
or in the CONFDIR/colorschemes/ directory"""
from ranger.ext.get_all_modules import get_all_modules
from os.path import expanduser, dirname, exists, join

__all__ = get_all_modules(dirname(__file__))

from ranger.colorschemes import *

confpath = expanduser('~/.ranger')
if exists(join(confpath, 'colorschemes')):
	initpy = join(confpath, 'colorschemes/__init__.py')
	if not exists(initpy):
		open(initpy, 'w').write("""# Automatically generated:
from ranger.ext.get_all_modules import get_all_modules
from os.path import dirname

__all__ = get_all_modules(dirname(__file__))
""")

	try:
		import sys
		sys.path[0:0] = [confpath]
		from colorschemes import *
	except ImportError:
		pass

