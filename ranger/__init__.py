"""Ranger - file browser for the unix terminal"""

__copyright__ = 'none'
__license__ = 'GPL'
__version__ = '1.0.0'
__credits__ = 'hut'
__author__ = 'hut'
__maintainer__ = 'hut'
__email__ = 'hut@lavabit.com'

import os
import sys

# for easier access
from ranger.ext.log import log

CONFDIR = os.path.expanduser('~/.ranger')
RANGERDIR = os.path.dirname(__file__)

sys.path.append(CONFDIR)
