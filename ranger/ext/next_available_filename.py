# Copyright (C) 2011  Roman Zimbelmann <romanz@lavabit.com>
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

import os.path

def next_available_filename(fname, directory="."):
	existing_files = os.listdir(directory)

	if fname not in existing_files:
		return fname
	if not fname.endswith("_"):
		fname += "_"
		if fname not in existing_files:
			return fname

	for i in range(1, len(existing_files) + 1):
		if fname + str(i) not in existing_files:
			return fname + str(i)
