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

"""Ranger - file browser for the unix terminal"""

import os
import sys

# for easier access
from ranger.ext.debug import log, trace

__copyright__ = 'none'
__license__ = 'ISC'
__version__ = '1.0.2'
__credits__ = 'hut'
__author__ = 'hut'
__maintainer__ = 'hut'
__email__ = 'hut@lavabit.com'

CONFDIR = os.path.expanduser('~/.ranger')
RANGERDIR = os.path.dirname(__file__)

sys.path.append(CONFDIR)

USAGE = '''%s [options] [path/filename]'''

from ranger.__main__ import main
