"""Workaround to allow running single test cases directly"""
try:
	from __init__ import init, Fake, OK, raise_ok
except:
	from test import init, Fake, OK, raise_ok
