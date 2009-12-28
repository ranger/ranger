def waitpid_no_intr(pid):
	"""catch interrupts which occur while using os.waitpid"""
	import os, errno

	while True:
		try:
			return os.waitpid(pid, 0)
		except KeyboardInterrupt:
			continue
		except OSError as e:
			if e.errno == errno.EINTR:
				continue
			else:
				raise
