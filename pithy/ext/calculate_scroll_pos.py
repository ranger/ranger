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


def calculate_scroll_pos(maxrows, nrows, index, previous, padding=3):
	"""
	Calculate the boundary for a scrollable window, specifically the
	index of the first dislpayed row.

	Arguments:
	maxrows     - the number of rows which fit in at most
	nrows       - the number of rows to be displayed
	index       - the index of a row that *needs* to be displayed
	previous    - the first displayed row before this operation
	padding     - padding between the top and bottom borders and the index
	"""
	halfmaxrows = maxrows // 2
	actual_index = index - previous
	upper_limit = maxrows - 1 - padding
	lower_limit = padding

	# correct a negative overflow
	if previous < 0:
		return 0

	# data fits into available space, no need to scroll at all
	if nrows < maxrows:
		return 0

	# large padding will invariably force the index to the center
	if halfmaxrows < padding:
		return min( nrows - maxrows, max( 0, index - halfmaxrows ))

	# first row was way too far down, probably after a resize of maxrows
	if previous > nrows - maxrows:
		return calculate_scroll_pos(maxrows, nrows, index,
				nrows - maxrows, padding)

	# scroll down
	if actual_index > upper_limit:
		return min( nrows - maxrows,
				previous + (actual_index - upper_limit))

	# scroll up
	if actual_index < lower_limit:
		return max( 0,
				previous - (lower_limit - actual_index))

	# actual index is inside the proper boundaries, make no change
	return previous
