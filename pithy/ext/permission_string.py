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

def permission_string(mode):
	return ''.join([
		"0pcCd?bB-?l?s???"[(mode & 0o170000) >> 12],
		mode & 0o0400 and 'r' or '-',
		mode & 0o0200 and 'w' or '-',
		mode & 0o0100 and (mode & 0o4000 and 's' or 'x') or
						  (mode & 0o4000 and 'S' or '-'),
		mode & 0o0040 and 'r' or '-',
		mode & 0o0020 and 'w' or '-',
		mode & 0o0010 and (mode & 0o2000 and 's' or 'x') or
						  (mode & 0o2000 and 'S' or '-'),
		mode & 0o0004 and 'r' or '-',
		mode & 0o0002 and 'w' or '-',
		mode & 0o0001 and (mode & 0o1000 and 't' or 'x') or
						  (mode & 0o1000 and 'T' or '-')])
