# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
The statusbar displays information about the current file and directory.

On the left side, there is a display similar to what "ls -l" would
print for the current file.  The right side shows directory information
such as the space used by all the files in this directory.
"""

from pwd import getpwuid
from grp import getgrgid
from os import getuid
from time import strftime, localtime

from ranger.ext.human_readable import human_readable
from . import Widget
from ranger.gui.bar import Bar

class StatusBar(Widget):
	__doc__ = __doc__
	owners = {}
	groups = {}
	timeformat = '%Y-%m-%d %H:%M'
	hint = None
	msg = None

	old_cf = None
	old_mtime = None
	old_du = None
	old_hint = None
	result = None

	def __init__(self, win, column=None):
		Widget.__init__(self, win)
		self.column = column
	
	def notify(self, text, duration=4, bad=False):
		self.msg = Message(text, duration, bad)
	
	def draw(self):
		"""Draw the statusbar"""

		if self.hint and isinstance(self.hint, str):
			if self.old_hint != self.hint:
				self.need_redraw = True
			if self.need_redraw:
				self._draw_hint()
			return

		if self.old_hint and not self.hint:
			self.old_hint = None
			self.need_redraw = True

		if self.msg:
			if self.msg.is_alive():
				self._draw_message()
				return
			else:
				self.msg = None
				self.need_redraw = True

		try:
			mtime = self.env.cf.stat.st_mtime
		except:
			mtime = -1

		if not self.result:
			self.need_redraw = True

		if self.old_du and not self.env.pwd.disk_usage:
			self.old_du = self.env.pwd.disk_usage
			self.need_redraw = True

		if self.old_cf != self.env.cf:
			self.old_cf = self.env.cf
			self.need_redraw = True

		if self.old_mtime != mtime:
			self.old_mtime = mtime
			self.need_redraw = True

		if self.need_redraw:
			self.need_redraw = False

			self._calc_bar()
			self._print_result(self.result)
	
	def _calc_bar(self):
		bar = Bar('in_statusbar')
		self._get_left_part(bar)
		self._get_right_part(bar)
		bar.shrink_by_removing(self.wid)

		self.result = bar.combine()
	
	def _draw_message(self):
		self.win.erase()
		self.color('in_statusbar', 'message',
				self.msg.bad and 'bad' or 'good')
		self.addnstr(0, 0, self.msg.text, self.wid)

	def _draw_hint(self):
		self.win.erase()
		highlight = True
		space_left = self.wid
		starting_point = self.x
		for string in self.hint.split('//'):
			highlight = not highlight
			if highlight:
				self.color('in_statusbar', 'text', 'highlight')
			else:
				self.color('in_statusbar', 'text')

			try:
				self.addnstr(0, starting_point, string, space_left)
			except:
				break
			space_left -= len(string)
			starting_point += len(string)
#			if starting_point >= self.wid:
#				break

	def _get_left_part(self, bar):
		left = bar.left
		
		if self.column is not None:
			target = self.column.target.pointed_obj
		else:
			target = self.env.at_level(0).pointed_obj

		if target is None:
			return

		if target.accessible is False:
			return

		perms = target.get_permission_string()
		how = getuid() == target.stat.st_uid and 'good' or 'bad'
		left.add(perms, 'permissions', how)

		left.add_space()
		left.add(str(target.stat.st_nlink), 'nlink')
		left.add_space()
		left.add(self._get_owner(target), 'owner')
		left.add_space()
		left.add(self._get_group(target), 'group')
		left.add_space()

		if target.islink:
			how = target.exists and 'good' or 'bad'
			left.add('-> ' + target.readlink, 'link', how)
		else:
			left.add(strftime(self.timeformat,
					localtime(target.stat.st_mtime)), 'mtime')
	
	def _get_owner(self, target):
		uid = target.stat.st_uid

		try:
			return self.owners[uid]
		except KeyError:
			try:
				self.owners[uid] = getpwuid(uid)[0]
				return self.owners[uid]
			except KeyError:
				return str(uid)

	def _get_group(self, target):
		gid = target.stat.st_gid

		try:
			return self.groups[gid]
		except KeyError:
			try:
				self.groups[gid] = getgrgid(gid)[0]
				return self.groups[gid]
			except KeyError:
				return str(gid)

	def _get_right_part(self, bar):
		right = bar.right
		if self.column is None:
			return

		target = self.column.target

		if not target.content_loaded or not target.accessible:
			return

		pos = target.scroll_begin
		max_pos = len(target) - self.column.hei
		base = 'scroll'

		right.add(human_readable(target.disk_usage, seperator=''))
		right.add(", ", "space")
		right.add(human_readable(self.env.get_free_space(target.mount_path),
			seperator=''))
		right.add("  ", "space")

		if target.marked_items:
			# Indicate that there are marked files. Useful if you scroll
			# away and don't see them anymore.
			right.add('Mrk', base, 'marked')
		elif max_pos > 0:
			if pos == 0:
				right.add('Top', base, 'top')
			elif pos >= max_pos:
				right.add('Bot', base, 'bot')
			else:
				right.add('{0:0>.0f}%'.format(100.0 * pos / max_pos),
						base, 'percentage')
		else:
			right.add('All', base, 'all')

	def _print_result(self, result):
		import _curses
		self.win.move(0, 0)
		for part in result:
			self.color(*part.lst)
			self.addstr(part.string)
		self.color_reset()

from time import time
class Message(object):
	elapse = None
	text = None
	bad = False

	def __init__(self, text, duration, bad):
		self.text = text
		self.bad = bad
		self.elapse = time() + duration
	
	def is_alive(self):
		return time() <= self.elapse
