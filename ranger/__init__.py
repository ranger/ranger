"""Ranger - file browser for the unix terminal"""
import os
import sys

# for easier access
from ranger.ext.debug import log, trace

__copyright__ = 'none'
__license__ = 'GPL'
__version__ = '1.0.0'
__credits__ = 'hut'
__author__ = 'hut'
__maintainer__ = 'hut'
__email__ = 'hut@lavabit.com'

CONFDIR = os.path.expanduser('~/.ranger')
RANGERDIR = os.path.dirname(__file__)

sys.path.append(CONFDIR)

USAGE = '''%s [options] [path/filename]'''

from ranger.__main__ import main
