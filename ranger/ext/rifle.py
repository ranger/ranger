# Copyright (C) 2012  Roman Zimbelmann <romanz@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

import os.path
import re, sys
from subprocess import Popen, PIPE
from ranger.ext.shell_escape import shell_quote
from ranger.ext.spawn import spawn
from ranger.ext.get_executables import get_executables
import time

def _is_terminal():
	try:
		os.ttyname(0)
		os.ttyname(1)
		os.ttyname(2)
	except:
		return False
	return True

class Rifle(object):
	delimiter1 = '='
	delimiter2 = ','

	def hook_before_executing(self, command, mimetype, flags):
		pass

	def hook_after_executing(self, command, mimetype, flags):
		pass

	def hook_command_preprocessing(self, command):
		return command

	def hook_command_postprocessing(self, command):
		return command

	def hook_environment(self, env):
		return env

	def hook_logger(self, string):
		sys.stderr.write(string + "\n")

	def __init__(self, config_file):
		self.config_file = config_file
		self._app_flags = False

	def reload_config(self, config_file=None):
		if config_file is None:
			config_file = self.config_file
		f = open(config_file, 'r')
		self.rules = []
		lineno = 1
		for line in f:
			if line.startswith('#') or line == '\n':
				continue
			line = line.strip()
			if self.delimiter1 not in line:
				self.hook_logger("Syntax error in %s line %d" % \
						(config_file, lineno))
			tests, command = line.split(self.delimiter1, 1)
			tests = tests.split(self.delimiter2)
			tests = tuple(tuple(f.strip().split(None, 1)) for f in tests)
			tests = tuple(tests)
			command = command.strip()
			self.rules.append((command, tests))
			lineno += 1

	def _eval_rule(self, rule, files, label):
		function = rule[0]
		argument = rule[1] if len(rule) > 1 else ''
		if not files:
			return False

		self._app_flags = ''

		if function == 'ext':
			extension = os.path.basename(files[0]).rsplit('.', 1)[-1]
			return bool(re.search('^' + argument + '$', extension))
		if function == 'name':
			return bool(re.search(argument, os.path.basename(files[0])))
		if function == 'path':
			return bool(re.search(argument, os.path.abspath(files[0])))
		if function == 'mime':
			return bool(re.search(argument, self._get_mimetype(files[0])))
		if function == 'has':
			return argument in get_executables()
		if function == 'terminal':
			return _is_terminal()
		if function == 'label':
			if label:
				self._found_label = argument == label
			else:
				# don't care about label in this case
				self._found_label = True
			return self._found_label
		if function == 'flag':
			self._app_flags = argument
			return True
		if function == 'X':
			return 'DISPLAY' in os.environ
		if function == 'else':
			return True

	def _get_mimetype(self, fname):
		if self._mimetype:
			return self._mimetype
		mimetype = spawn("file", "--mime-type", "-Lb", fname)
		self._mimetype = mimetype
		return mimetype

	def _build_command(self, files, action):
		flags = self._app_flags
		_filenames = "' '".join(f.replace("'", "'\\\''") for f in files)
		command = "set -- '%s'" % _filenames + '\n'
		if 'p' in flags and not 'f' in flags and _is_terminal():
			action += '| less'
		if 'f' in flags:
			action = "nohup %s >&/dev/null &" % action
		command += action
		return command

	def list_commands(self, files, mimetype=None):
		self._mimetype = mimetype
		command = None
		count = 0
		result = []
		t = time.time()
		for cmd, tests in self.rules:
			for test in tests:
				if not self._eval_rule(test, files, None):
					break
			else:
				result.append((count, cmd, self._app_flags))
				count += 1
		#sys.stderr.write("%f\n" % (time.time() - t))
		return result

	def execute(self, files, number=0, label=None, mimetype=None):
		self._mimetype = mimetype
		self._found_label = True
		command = None
		count = 0
		for cmd, tests in self.rules:
			if label:
				self._found_label = False
			for test in tests:
				if not self._eval_rule(test, files, label):
					#print("fails on test %s" % str(test))
					break
			else:
				if not self._found_label:
					pass
				elif count != number:
					count += 1
				else:
					command = self.hook_command_preprocessing(command)
					command = self._build_command(files, cmd)
					break
		#print(command)
		if command is not None:
			command = self.hook_command_postprocessing(command)
			self.hook_before_executing(command, self._mimetype, self._app_flags)
			try:
				p = Popen(command, shell=True)
				p.wait()
			finally:
				self.hook_after_executing(command, self._mimetype, self._app_flags)

		else:
			self.hook_logger("No action found.")

if __name__ == '__main__':
	import sys
	rifle = Rifle(os.environ['HOME'] + '/.config/ranger/rifle.conf')
	rifle.reload_config()
	#print(rifle.list_commands(sys.argv[1:]))
	rifle.execute(sys.argv[1:], number=0)
