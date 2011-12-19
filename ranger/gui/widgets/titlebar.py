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

"""
The titlebar is the widget at the top, giving you broad overview.

It displays the current path among other things.
"""

from os.path import basename

from . import Widget
from ranger.gui.bar import Bar

class TitleBar(Widget):
	old_cf = None
	old_keybuffer = None
	old_wid = None
	result = None
	throbber = ' '
	need_redraw = False
	tab_width = 0

	def __init__(self, *args, **keywords):
		Widget.__init__(self, *args, **keywords)
		self.fm.signal_bind('tab.change', self.request_redraw, weak=True)

	def request_redraw(self):
		self.need_redraw = True

	def draw(self):
		if self.need_redraw or \
				self.env.cf != self.old_cf or\
				str(self.env.keybuffer) != str(self.old_keybuffer) or\
				self.wid != self.old_wid:
			self.need_redraw = False
			self.old_wid = self.wid
			self.old_cf = self.env.cf
			self._calc_bar()
		self._print_result(self.result)
		if self.wid > 2:
			self.color('in_titlebar', 'throbber')
			self.addnstr(self.y, self.wid - 2 - self.tab_width,
					self.throbber, 1)

	def click(self, event):
		"""Handle a MouseEvent"""
		direction = event.mouse_wheel_direction()
		if direction:
			self.fm.tab_move(direction)
			self.need_redraw = True
			return True

		if not event.pressed(1) or not self.result:
			return False

		pos = self.wid - 1
		for tabname in reversed(self.fm._get_tab_list()):
			tabtext = self._get_tab_text(tabname)
			pos -= len(tabtext)
			if event.x > pos:
				self.fm.tab_open(tabname)
				self.need_redraw = True
				return True

		pos = 0
		for i, part in enumerate(self.result):
			pos += len(part)
			if event.x < pos:
				if i < 2:
					self.fm.enter_dir("~")
				elif i == 2:
					self.fm.enter_dir("/")
				else:
					try:
						self.fm.enter_dir(part.directory)
					except:
						pass
				return True
		return False

	def _calc_bar(self):
		bar = Bar('in_titlebar')
		self._get_left_part(bar)
		self._get_right_part(bar)
		try:
			bar.shrink_from_the_left(self.wid)
		except ValueError:
			bar.shrink_by_removing(self.wid)
		self.result = bar.combine()

	def _get_left_part(self, bar):
		# TODO: Properly escape non-printable chars without breaking unicode
		if self.env.username == 'root':
			clr = 'bad'
		else:
			clr = 'good'

		bar.add(self.env.username, 'hostname', clr, fixed=True)
		bar.add('@', 'hostname', clr, fixed=True)
		bar.add(self.env.hostname, 'hostname', clr, fixed=True)
		bar.add(':', 'hostname', clr, fixed=True)

		pathway = self.env.pathway
		if self.settings.tilde_in_titlebar and \
				self.fm.env.cwd.path.startswith(self.env.home_path):
			pathway = pathway[self.env.home_path.count('/')+1:]
			bar.add('~/', 'directory', fixed=True)

		for path in pathway:
			if path.is_link:
				clr = 'link'
			else:
				clr = 'directory'

			bar.add(path.basename, clr, directory=path)
			bar.add('/', clr, fixed=True, directory=path)

		if self.env.cf is not None:
			bar.add(self.env.cf.basename, 'file')

	def _get_right_part(self, bar):
		# TODO: fix that pressed keys are cut off when chaining CTRL keys
		kb = str(self.env.keybuffer)
		self.old_keybuffer = kb
		bar.addright(kb, 'keybuffer', fixed=True)
		bar.addright('  ', 'space', fixed=True)
		self.tab_width = 0
		if len(self.fm.tabs) > 1:
			for tabname in self.fm._get_tab_list():
				tabtext = self._get_tab_text(tabname)
				self.tab_width += len(tabtext)
				clr = 'good' if tabname == self.fm.current_tab else 'bad'
				bar.addright(tabtext, 'tab', clr, fixed=True)

	def _get_tab_text(self, tabname):
		result = ' ' + str(tabname)
		if self.settings.dirname_in_tabs:
			dirname = basename(self.fm.tabs[tabname])
			if not dirname:
				result += ":/"
			elif len(dirname) > 15:
				result += ":" + dirname[:14] + "~"
			else:
				result += ":" + dirname
		return result

	def _print_result(self, result):
		self.win.move(0, 0)
		for part in result:
			self.color(*part.lst)
			y, x = self.win.getyx()
			self.addstr(y, x, str(part))
		self.color_reset()
