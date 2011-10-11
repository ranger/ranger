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

from os import symlink, sep

def relative_symlink(src, dst):
	common_base = get_common_base(src, dst)
	symlink(get_relative_source_file(src, dst, common_base), dst)

def get_relative_source_file(src, dst, common_base=None):
	if common_base is None:
		common_base = get_common_base(src, dst)
	return '../' * dst.count('/', len(common_base)) + src[len(common_base):]

def get_common_base(src, dst):
	if not src or not dst:
		return '/'
	i = 0
	while True:
		new_i = src.find(sep, i + 1)
		if new_i == -1:
			break
		if not dst.startswith(src[:new_i + 1]):
			break
		i = new_i
	return src[:i + 1]
