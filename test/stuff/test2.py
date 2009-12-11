from code import cli
import signal

with cli.lock:
	with cli.lock:
		print("this will be delayed forever")
	print("hi!")
