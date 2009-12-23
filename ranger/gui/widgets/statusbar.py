"""The StatusBar displays information about the currently selected file
in the same form as the "ls -l" command on the left side, and
some additional info about the current directory on the right side.
"""

from . import Widget
from ranger import log
from pwd import getpwuid
from grp import getgrgid
from os import getuid
from time import strftime, localtime

class StatusBar(Widget):
	__doc__ = __doc__
	owners = {}
	groups = {}
	timeformat = '%Y-%m-%d %H:%M'

	def __init__(self, win, filelist=None):
		Widget.__init__(self, win)
		self.filelist = filelist
	
	def draw(self):
		"""Draw the statusbar"""

		# each item in the returned array looks like:
		# [ list_with_color_tags,       string       ]
		# [ ['permissions', 'allowed'], '-rwxr-xr-x' ]
		left = self._get_left_part()
		right = self._get_right_part()
		self._print_result(self._combine_parts(left, right))

	def _get_left_part(self):
		part = []

		if self.filelist is not None:
			target = self.filelist.target.pointed_file
		else:
			target = self.env.at_level(0).pointed_file

		if target is None:
			return part

		if target.accessible is False:
			return part

		perms = target.get_permission_string()
		color = ['permissions']
		if getuid() == target.stat.st_uid:
			color.append('good')
		else:
			color.append('bad')
		part.append([color, perms])

		part.append([['space'], " "])
		part.append([['nlink'], str(target.stat.st_nlink)])
		part.append([['space'], " "])
		part.append([['owner'], self._get_owner(target)])
		part.append([['space'], " "])
		part.append([['group'], self._get_group(target)])
		part.append([['space'], " "])
		if target.islink:
			color = ['link']
			color.append(target.exists and 'good' or 'bad')
			part.append([color, '-> ' + target.readlink])
		else:
			part.append([['mtime'], strftime(self.timeformat, \
					localtime(target.stat.st_mtime))])
		return part
	
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

	def _get_right_part(self):
		part = []
		if self.filelist is None:
			return part

		target = self.filelist.target
#		target = self.env.at_level(0)

		if not target.content_loaded or not target.accessible:
			return part

		pos = target.scroll_begin
		max_pos = len(target) - self.filelist.hei

		if target.marked_items:
			part.append([['scroll', 'marked'], 'Mrk'])
		elif max_pos > 0:
			if pos == 0:
				part.append([['scroll', 'top'], 'Top'])
			elif pos >= max_pos:
				part.append([['scroll', 'bot'], 'Bot'])
			else:
				part.append([['scroll', 'percentage'], \
					'{0:0>.0f}%'.format(100.0 * pos / max_pos)])
		else:
			part.append([['scroll', 'all'], 'All'])
		return part

	def _combine_parts(self, left, right):
		"""Combines left and right, filling the middle with spaces and
		removing elements which don't have enough room to fit in.
		<left> will be turned into the result (which is also returned).
		"""

		leftsize = sum(len(part[1]) for part in left)
		rightsize = sum(len(part[1]) for part in right)
		sumsize = leftsize + rightsize

		# remove elemets from the left until it fits
		if sumsize > self.wid:
			while len(left) > 0:
				leftsize -= len(left.pop(-1)[1])
				if leftsize + rightsize <= self.wid:
					break
			sumsize = leftsize + rightsize

			# remove elemets from the right until it fits
			if sumsize > self.wid:
				while len(right) > 0:
					rightsize -= len(right.pop(0)[1])
					if leftsize + rightsize <= self.wid:
						break
				sumsize = leftsize + rightsize

		if sumsize < self.wid:
			left.append([ ['space'], " " * (self.wid - sumsize) ])
		left.extend(right)
		return left

	def _print_result(self, result):
		import _curses
		self.win.move(self.y, self.x)
		for part in result:
			self.color('in_statusbar', *part[0])
			try:
				self.win.addstr(part[1])
			except _curses.error:
				pass
