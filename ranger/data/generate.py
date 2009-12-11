#!/usr/bin/python3
# coding=utf-8

if __name__ == '__main__':
	import sys, pickle

	protocol = 0
	table = {}

	for line in open(len(sys.argv) > 1 and sys.argv[1] or "mime.types"):
		if len(line) > 3 and line[0] != '#' and '\t' in line:
			name, *extensions = line.split()
			for ext in extensions:
				table[ext] = name

	pickle.dump(table, open('mime.dat', 'wb'), protocol)
