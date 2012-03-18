#!/usr/bin/python
# Copyright (C) 2012  Roman Zimbelmann <romanz@lavabit.com>
# This software is distributed under the terms of the GNU GPL version 3.

"""
rifle, the file executor/opener of ranger

This can be used as a standalone program or can be embedded in python code.
When used together with ranger, it doesn't have to be installed to $PATH.

You can use this program without installing ranger by inlining the imported
ranger functions. (shell_quote, spawn, ...)

Example usage:

	rifle = Rifle("rilfe.conf")
	rifle.reload_config()
	rifle.execute(["file1", "file2"])
"""

import os.path
import re, sys
from subprocess import Popen, PIPE
from ranger.ext.shell_escape import shell_quote
from ranger.ext.spawn import spawn
from ranger.ext.get_executables import get_executables
import time

def _is_terminal():
	# Check if stdin (file descriptor 0), stdout (fd 1) and
	# stderr (fd 2) are connected to a terminal
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
		"""Replace the current configuration with the one in config_file"""
		if config_file is None:
			config_file = self.config_file
		f = open(config_file, 'r')
		self.rules = []
		lineno = 1
		for line in f:
			if line.startswith('#') or line == '\n':
				continue
			line = line.strip()
			try:
				if self.delimiter1 not in line:
					raise Exception("Line without delimiter")
				tests, command = line.split(self.delimiter1, 1)
				tests = tests.split(self.delimiter2)
				tests = tuple(tuple(f.strip().split(None, 1)) for f in tests)
				tests = tuple(tests)
				command = command.strip()
				self.rules.append((command, tests))
			except Exception as e:
				self.hook_logger("Syntax error in %s line %d (%s)" % \
					(config_file, lineno, str(e)))
			lineno += 1
		f.close()

	def _eval_condition(self, condition, files, label):
		# Handle the negation of conditions starting with an exclamation mark,
		# then pass on the arguments to _eval_condition2().

		if condition[0].startswith('!'):
			new_condition = tuple([condition[0][1:]]) + tuple(condition[1:])
			return not self._eval_condition2(new_condition, files, label)
		return self._eval_condition2(condition, files, label)

	def _eval_condition2(self, rule, files, label):
		# This function evaluates the condition, after _eval_condition() handled
		# negation of conditions starting with a "!".

		function = rule[0]
		argument = rule[1] if len(rule) > 1 else ''
		if not files:
			return False

		self._app_flags = ''
		self._app_label = None

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
			self._app_label = argument
			if label:
				return argument == label
			return True
		if function == 'flag':
			self._app_flags = argument
			return True
		if function == 'X':
			return 'DISPLAY' in os.environ
		if function == 'else':
			return True

	def _get_mimetype(self, fname):
		# Spawn "file" to determine the mime-type of the given file.
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
		"""
		Returns one 4-tuple for all currently applicable commands
		The 4-tuple contains (count, command, label, flags).
		count is the index, counted from 0 upwards,
		command is the command that will be executed.
		label and flags are the label and flags specified in the rule.
		"""
		self._mimetype = mimetype
		count = 0
		result = []
		t = time.time()
		for cmd, tests in self.rules:
			for test in tests:
				if not self._eval_condition(test, files, None):
					break
			else:
				result.append((count, cmd, self._app_label, self._app_flags))
				count += 1
		return result

	def execute(self, files, way=0, label=None, flags=None, mimetype=None):
		"""
		Executes the given list of files.

		The default way to run files is 0.  Specifying way=N means rifle should
		execute the Nth command whose conditions match for the given files.

		If a label is specified, only rules with this label will be considered.
		Specifying the mimetype will override the mimetype returned by `file`.

		By specifying a flag, you extend the flag that is defined in the rule.
		Uppercase flags negate the respective lowercase flags.
		For example: if the flag in the rule is "pw" and you specify "Pf", then
		the "p" flag is negated and the "f" flag is added, resulting in "wf".
		"""
		self._mimetype = mimetype
		command = None
		count = 0
		# Determine command
		for cmd, tests in self.rules:
			for test in tests:
				if not self._eval_condition(test, files, label):
					break
			else:
				if count != way:
					count += 1
				else:
					command = self.hook_command_preprocessing(command)
					command = self._build_command(files, cmd)
					break
		# Execute command
		if command is None:
			if count <= 0:
				self.hook_logger("No action found.")
			else:
				self.hook_logger("Method number %d is undefined." % way)
		else:
			command = self.hook_command_postprocessing(command)
			self.hook_before_executing(command, self._mimetype, self._app_flags)
			try:
				p = Popen(command, shell=True)
				p.wait()
			finally:
				self.hook_after_executing(command, self._mimetype, self._app_flags)

def main():
	"""The main function, which is run when you start this program direectly."""
	import sys

	# Find configuration file path
	if 'XDG_CONFIG_HOME' in os.environ and os.environ['XDG_CONFIG_HOME']:
		conf_path = os.environ['XDG_CONFIG_HOME'] + '/ranger/rifle.conf'
	else:
		conf_path = os.path.expanduser('~/.config/ranger/rifle.conf')
	if not os.path.isfile(conf_path):
		conf_path = os.path.normpath(os.path.join(os.path.dirname(__file__),
			'../defaults/rifle.conf'))

	# Evaluate arguments
	from optparse import OptionParser
	parser = OptionParser(usage="%prog [-hlpw] [files]")
	parser.add_option('-p', type='string', default='0', metavar="KEYWORD",
			help="pick a method to open the files.  KEYWORD is either the number"
			" listed by 'rifle -l' or a string that matches a label in the"
			" configuration file")
	parser.add_option('-l', action="store_true",
			help="list possible ways to open the files")
	parser.add_option('-w', type='string', default=None, metavar="PROGRAM",
			help="open the files with PROGRAM")
	options, positional = parser.parse_args()

	if options.p.isdigit():
		way = int(options.p)
		label = None
	else:
		way = 0
		label = options.p

	if options.w is not None and not options.l:
		p = Popen([options.w] + list(positional))
		p.wait()
	else:
		# Start up rifle
		rifle = Rifle(conf_path)
		rifle.reload_config()
		#print(rifle.list_commands(sys.argv[1:]))
		if options.l:
			for count, cmd, label, flags in rifle.list_commands(sys.argv[1:]):
				print("%d: %s" % (count, cmd))
		else:
			rifle.execute(sys.argv[1:], way=way, label=label)


if __name__ == '__main__':
	main()
