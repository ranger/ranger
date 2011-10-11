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

from ranger.gui.color import *
from ranger.colorschemes.default import Default

class Scheme(Default):
	def use(self, context):
		fg, bg, attr = Default.use(self, context)

		if context.directory and not context.marked and not context.link:
			fg = green

		if context.in_titlebar and context.hostname:
			fg = red if context.bad else blue

		return fg, bg, attr
