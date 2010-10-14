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
import sys
rangerpath = os.path.join(os.path.dirname(__file__), '..')
if sys.path[1] != rangerpath:
	sys.path[1:1] = [rangerpath]

import unittest
import gc
from ranger.ext.signals import *

class TestSignal(unittest.TestCase):
	def setUp(self):
		self.sd = SignalDispatcher()

	def test_signal_register_emit(self):
		sd = self.sd
		def poo(sig):
			self.assert_('works' in sig)
			self.assertEqual('yes', sig.works)
		handler = sd.signal_bind('x', poo)

		sd.signal_emit('x', works='yes')
		sd.signal_unbind(handler)
		sd.signal_emit('x')

	def test_signal_order(self):
		sd = self.sd
		lst = []
		def addn(n):
			return lambda _: lst.append(n)

		sd.signal_bind('x', addn(6))
		sd.signal_bind('x', addn(3), priority=1)
		sd.signal_bind('x', addn(2), priority=1)
		sd.signal_bind('x', addn(9), priority=0)
		sd.signal_bind('x', addn(1337), priority=0.7)
		sd.signal_emit('x')

		self.assert_(lst.index(3) < lst.index(6))
		self.assert_(lst.index(2) < lst.index(6))
		self.assert_(lst.index(6) < lst.index(9))
		self.assert_(lst.index(1337) < lst.index(6))
		self.assert_(lst.index(1337) < lst.index(9))
		self.assert_(lst.index(1337) > lst.index(2))

	def test_modifying_arguments(self):
		sd = self.sd
		lst = []
		def modify(s):
			s.number = 5
		def set_number(s):
			lst.append(s.number)
		def stopit(s):
			s.stop()

		sd.signal_bind('setnumber', set_number)
		sd.signal_emit('setnumber', number=100)
		self.assertEqual(100, lst[-1])

		sd.signal_bind('setnumber', modify, priority=1)
		sd.signal_emit('setnumber', number=100)
		self.assertEqual(5, lst[-1])

		lst.append(None)
		sd.signal_bind('setnumber', stopit, priority=1)
		sd.signal_emit('setnumber', number=100)
		self.assertEqual(None, lst[-1])

	def test_weak_refs(self):
		sd = self.sd
		is_deleted = [False]

		class Foo(object):
			def __init__(self):
				self.alphabet = ['a']
			def calc(self, signal):
				self.alphabet.append(chr(ord(self.alphabet[-1]) + 1))
			def __del__(self):
				is_deleted[0] = True

		foo = Foo()
		alphabet = foo.alphabet
		calc = foo.calc

		del foo
		self.assertEqual('a', ''.join(alphabet))
		sd.signal_bind('mysignal', calc, weak=True)
		sd.signal_emit('mysignal')
		self.assertEqual('ab', ''.join(alphabet))
		self.assertFalse(is_deleted[0])

		del calc
		self.assertTrue(is_deleted[0])

	def test_weak_refs_dead_on_arrival(self):
		sd = self.sd
		is_deleted = [False]

		class Foo(object):
			def __init__(self):
				self.alphabet = ['a']
			def calc(self, signal):
				self.alphabet.append(chr(ord(self.alphabet[-1]) + 1))
			def __del__(self):
				is_deleted[0] = True

		foo = Foo()
		alphabet = foo.alphabet

		self.assertEqual('a', ''.join(alphabet))
		sd.signal_bind('mysignal', foo.calc, weak=True)

		sd.signal_emit('mysignal')
		self.assertEqual('ab', ''.join(alphabet))
		self.assertFalse(is_deleted[0])

		del foo

		sd.signal_emit('mysignal')
		self.assertEqual('ab', ''.join(alphabet))
		self.assertTrue(is_deleted[0])

if __name__ == '__main__':
	unittest.main()
