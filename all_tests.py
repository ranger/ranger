#!/usr/bin/python
"""Run all the tests inside the test/ directory as a test suite."""
if __name__ == '__main__':
	import unittest
	from test import *
	from sys import exit, argv

	try:
		verbosity = int(argv[1])
	except IndexError:
		verbosity = 2

	tests = []
	for key, val in vars().copy().items():
		if key.startswith('tc_'):
			tests.extend(v for k,v in vars(val).items() if type(v) == type)

	suite = unittest.TestSuite(map(unittest.makeSuite, tests))
	result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
	if len(result.errors) + len(result.failures) > 0:
		exit(1)
