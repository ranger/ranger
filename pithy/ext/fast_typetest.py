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

import os.path

# Data:
AUDIO_EXTENSIONS = set(['aif', 'aifc', 'aiff', 'amr', 'au', 'awb', 'axa',
	'flac', 'gsm', 'kar', 'm3u', 'm4a', 'mid', 'midi', 'mp+', 'mp2',
	'mp3', 'mpc', 'mpega', 'mpga', 'mpp', 'oga', 'ogg', 'pls', 'ra',
	'ram', 'rm', 'sd2', 'sid', 'snd', 'spx', 'wav', 'wax', 'wma'])

CONTAINER_EXTENSIONS = set(['7z', 'ace', 'ar', 'arc', 'bz', 'bz2', 'cab',
	'cpio', 'cpt', 'dgc', 'dmg', 'gz', 'iso', 'jar', 'msi', 'pkg',
	'rar', 'shar', 'tar', 'tbz', 'tgz', 'xar', 'xz', 'zip'])

IMAGE_EXTENSIONS = set(['art', 'bmp', 'cdr', 'cdt', 'cpt', 'cr2', 'crw',
	'djv', 'djvu', 'erf', 'gif', 'ico', 'ief', 'jng', 'jpe', 'jpeg',
	'jpg', 'nef', 'orf', 'pat', 'pbm', 'pcx', 'pgm', 'png', 'pnm',
	'ppm', 'psd', 'ras', 'rgb', 'svg', 'svgz', 'tif', 'tiff', 'wbmp',
	'xbm', 'xpm', 'xwd'])

VIDEO_EXTENSIONS = set(['3gpp', 'asf', 'asx', 'avi', 'axv', 'dif', 'div',
	'divx', 'dl', 'dv', 'fli', 'flv', 'gl', 'lsf', 'lsx', 'mkv',
	'mng', 'mov', 'movie', 'mp4', 'mpe', 'mpeg', 'mpg', 'mpv', 'mxu',
	'ogm', 'ogv', 'qt', 'wm', 'wmv', 'wmx', 'wvx'])

# Shortcuts:
is_image     = IMAGE_EXTENSIONS.__contains__
is_video     = VIDEO_EXTENSIONS.__contains__
is_audio     = AUDIO_EXTENSIONS.__contains__
is_container = CONTAINER_EXTENSIONS.__contains__
