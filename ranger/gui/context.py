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

CONTEXT_KEYS = ['reset', 'error', 'badinfo',
		'in_browser', 'in_statusbar', 'in_titlebar', 'in_console',
		'in_pager', 'in_taskview',
		'directory', 'file', 'hostname',
		'executable', 'media', 'link', 'fifo', 'socket', 'device',
		'video', 'audio', 'image', 'media', 'document', 'container',
		'selected', 'empty', 'main_column', 'message', 'background',
		'good', 'bad',
		'space', 'permissions', 'owner', 'group', 'mtime', 'nlink',
		'scroll', 'all', 'bot', 'top', 'percentage', 'filter',
		'marked', 'tagged', 'tag_marker', 'cut', 'copied',
		'help_markup', # COMPAT
		'seperator', 'key', 'special', 'border', # COMPAT
		'title', 'text', 'highlight', 'bars', 'quotes', 'tab',
		'keybuffer']

class Context(object):
	def __init__(self, keys):
		# set all given keys to True
		d = self.__dict__
		for key in keys:
			d[key] = True

# set all keys to False
for key in CONTEXT_KEYS:
	setattr(Context, key, False)
