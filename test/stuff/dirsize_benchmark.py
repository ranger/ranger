import os, time
class Dirsize():
	def a(path):
		return len(os.listdir(path))

	def b(path):
		for _, dirs, files in os.walk(path):
			return len(files) + len(dirs)

	def c(path):
		first = next(os.walk(path))
		return len(first[1]) + len(first[2])

paths = {
		'/usr/lib': None,
		'/usr/bin': None,
		'/home/hut': None
}

for key in paths.keys():
	paths[key] = Dirsize.a(key) # assume Dirsize.a() returns a correct result
	for algo in ['a', 'b', 'c']:
		t = time.time()
		for i in range(4):
			assert Dirsize.__dict__[algo](key) == paths[key]
		print("algorithm %s: %20s: %f" % (algo, key, time.time() - t))

# a !!
