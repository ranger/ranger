#!/usr/bin/python3
# coding=utf-8

protocol = 0

import sys, pickle

table = {}
for line in open(len(sys.argv) > 1 and sys.argv[1] or "mime.types"):
	if len(line) > 3 and line[0] != '#' and '\t' in line:
		name, *extensions = line.split()
		for ext in extensions:
			table[ext] = name

pickle.dump(table, open('mime.dat', 'wb'), protocol)

