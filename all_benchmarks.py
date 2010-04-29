#!/usr/bin/python
"""Run all the tests inside the test/ directory as a test suite."""
if __name__ == '__main__':
	from test import *
	from time import time
	from types import FunctionType as function
	from sys import argv
	bms = []
	try:
		n = int(argv[1])
	except IndexError:
		n = 10
	for key, val in vars().copy().items():
		if key.startswith('bm_'):
			bms.extend(v for k,v in vars(val).items() if type(v) == type)
	for bmclass in bms:
		for attrname in vars(bmclass):
			if not attrname.startswith('bm_'):
				continue
			bmobj = bmclass()
			t1 = time()
			method = getattr(bmobj, attrname)
			methodname = "{0}.{1}".format(bmobj.__class__.__name__, method.__name__)
			try:
				method(n)
			except:
				print("{0} failed!".format(methodname))
				raise
			else:
				t2 = time()
				print("{0:60}: {1:10}s".format(methodname, t2 - t1))
