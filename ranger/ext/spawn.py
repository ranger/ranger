# Copyright (C) 2009, 2010, 2011  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from subprocess import Popen, PIPE
ENCODING = 'utf-8'

def spawn(*args):
	"""Runs a program, waits for its termination and returns its stdout"""
	if len(args) == 1:
		popen_arguments = args[0]
		shell = isinstance(popen_arguments, str)
	else:
		popen_arguments = args
		shell = False
	process = Popen(popen_arguments, stdout=PIPE, shell=shell)
	stdout, stderr = process.communicate()
	return stdout.decode(ENCODING)
