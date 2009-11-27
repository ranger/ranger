import random, time

class DelValue():
	def a(d):
		return dict((k, v) for k, v in d.items() if v is not 0)

	def b(d):
		for k, v in d.copy().items():
			if v == 0: del d[k]
		return d

	def c(d):
		for k in tuple(d.keys()):
			if d[k] == 0: del d[k]
		return d

	def d(d):
		for k, v in tuple(d.items()):
			if v == 0: del d[k]
		return d


basedict = {}
for i in range(200):
	basedict[i] = random.randint(0, 1)

expected = DelValue.a(basedict.copy())

for algo in ['a', 'b', 'c', 'd']:
	copy = basedict.copy()
	t = time.time()
	for i in range(100):
		assert DelValue.__dict__[algo](copy) == expected
	print("algorithm %s: %f" % (algo, time.time() - t))

# c it is, although b is faster with smaller dictionaries
