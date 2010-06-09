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

def TODO(fnc):
	def result(*arg, **kw):
		try:
			fnc(*arg, **kw)
		except:
			pass # failure expected
	return result

class Fake(object):
	def __getattr__(self, attrname):
		val = Fake()
		self.__dict__[attrname] = val
		return val

	def __call__(self, *_, **__):
		return Fake()

	def __clear__(self):
		self.__dict__.clear()

	def __iter__(self):
		return iter(())

class OK(Exception):
	pass

def raise_ok(*_, **__):
	raise OK()
