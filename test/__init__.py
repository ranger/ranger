import os, sys

__all__ = [ x[0:x.index('.')] \
		for x in os.listdir(os.path.dirname(__file__)) \
		if x.startswith('tc_') ]
