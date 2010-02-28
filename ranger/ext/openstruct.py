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

class OpenStruct(object):
	def __init__(self, __dictionary=None, **__keywords):
		if __dictionary:
			self.__dict__.update(__dictionary)
		if __keywords:
			self.__dict__.update(__keywords)

	def __getitem__(self, key):
		return self.__dict__[key]

	def __setitem__(self, key, value):
		self.__dict__[key] = value
		return value

	def __contains__(self, key):
		return key in self.__dict__

class ReferencedOpenStruct(OpenStruct):
	def __init__(self, dictionary):
		self.__dict__ = dictionary
