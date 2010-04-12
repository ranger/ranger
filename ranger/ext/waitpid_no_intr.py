# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
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

from errno import EINTR
from os import waitpid

def waitpid_no_intr(pid):
	"""catch interrupts which occur while using os.waitpid"""
	while True:
		try:
			return waitpid(pid, 0)
		except KeyboardInterrupt:
			continue
		except OSError as e:
			if e.errno == EINTR:
				continue
			else:
				raise
