#!/usr/bin/python3
"""Run all the tests inside the test/ directory as a test suite."""
if __name__ == '__main__':
	import unittest
	from test import *

	tests = []
	for key, val in vars().copy().items():
		if key.startswith('tc_'):
			tests.extend(v for k,v in vars(val).items() if type(v) == type)

	suite = unittest.TestSuite(map(unittest.makeSuite, tests))
	unittest.TextTestRunner(verbosity=2).run(suite)
