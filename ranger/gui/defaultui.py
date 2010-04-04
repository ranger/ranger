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

from ranger.gui.ui import UI

class DefaultUI(UI):
	def setup(self):
		"""Build up the UI by initializing widgets."""
		from ranger.gui.widgets.browserview import BrowserView
		from ranger.gui.widgets.titlebar import TitleBar
		from ranger.gui.widgets.console import Console
		from ranger.gui.widgets.statusbar import StatusBar
		from ranger.gui.widgets.taskview import TaskView
		from ranger.gui.widgets.pager import Pager

		# Create a title bar
		self.titlebar = TitleBar(self.win)
		self.add_child(self.titlebar)

		# Create the browser view
		self.browser = BrowserView(self.win, self.settings.column_ratios)
		self.settings.signal_bind('setopt.column_ratios',
				self.browser.change_ratios)
		self.add_child(self.browser)
		self.main_column = self.browser.main_column

		# Create the process manager
		self.taskview = TaskView(self.win)
		self.taskview.visible = False
		self.add_child(self.taskview)

		# Create the status bar
		self.status = StatusBar(self.win, self.browser.main_column)
		self.add_child(self.status)

		# Create the console
		self.console = Console(self.win)
		self.add_child(self.console)
		self.console.visible = False

		# Create the pager
		self.pager = Pager(self.win)
		self.pager.visible = False
		self.add_child(self.pager)

	def update_size(self):
		"""resize all widgets"""
		UI.update_size(self)
		y, x = self.env.termsize

		self.browser.resize(1, 0, y - 2, x)
		self.taskview.resize(1, 0, y - 2, x)
		self.pager.resize(1, 0, y - 2, x)
		self.titlebar.resize(0, 0, 1, x)
		self.status.resize(y - 1, 0, 1, x)
		self.console.resize(y - 1, 0, 1, x)

	def notify(self, *a, **k):
		return self.status.notify(*a, **k)

	def close_pager(self):
		if self.console.visible:
			self.console.focused = True
		self.pager.close()
		self.pager.visible = False
		self.pager.focused = False
		self.browser.visible = True

	def open_pager(self):
		if self.console.focused:
			self.console.focused = False
		self.pager.open()
		self.pager.visible = True
		self.pager.focused = True
		self.browser.visible = False
		return self.pager

	def open_embedded_pager(self):
		self.browser.open_pager()
		return self.browser.pager

	def close_embedded_pager(self):
		self.browser.close_pager()

	def open_console(self, mode, string=''):
		if self.console.open(mode, string):
			self.status.msg = None
			self.console.on_close = self.close_console
			self.console.visible = True
			self.status.visible = False

	def close_console(self):
		self.console.visible = False
		self.status.visible = True
		self.close_pager()

	def open_taskview(self):
		self.pager.close()
		self.pager.visible = False
		self.pager.focused = False
		self.console.visible = False
		self.browser.visible = False
		self.taskview.visible = True
		self.taskview.focused = True

	def redraw_main_column(self):
		self.browser.main_column.need_redraw = True

	def close_taskview(self):
		self.taskview.visible = False
		self.browser.visible = True
		self.taskview.focused = False

	def scroll(self, relative):
		if self.browser and self.browser.main_column:
			self.browser.main_column.scroll(relative)

	def throbber(self, string='.', remove=False):
		if remove:
			self.titlebar.throbber = type(self.titlebar).throbber
		else:
			self.titlebar.throbber = string

	def hint(self, text=None):
		self.status.hint = text
