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

import weakref
from types import MethodType

class Signal(dict):
	stopped = False
	def __init__(self, **keywords):
		dict.__init__(self, keywords)
		self.__dict__ = self

	def stop(self):
		self.stopped = True


class SignalHandler(object):
	active = True
	def __init__(self, signal_name, function, priority, pass_signal):
		self.priority = max(0, min(1, priority))
		self.signal_name = signal_name
		self.function = function
		self.pass_signal = pass_signal


class SignalDispatcher(object):
	def __init__(self):
		self._signals = dict()

	signal_clear = __init__

	def signal_bind(self, signal_name, function, priority=0.5, weak=False):
		assert isinstance(signal_name, str)
		try:
			handlers = self._signals[signal_name]
		except:
			handlers = self._signals[signal_name] = []
		nargs = function.__code__.co_argcount

		try:
			instance = function.__self__
		except:
			if weak:
				function = weakref.proxy(function)
		else:
			nargs -= 1
			if weak:
				function = (function.__func__, weakref.proxy(function.__self__))
		handler = SignalHandler(signal_name, function, priority, nargs > 0)
		handlers.append(handler)
		handlers.sort(key=lambda handler: -handler.priority)
		return handler

	def signal_unbind(self, signal_handler):
		try:
			handlers = self._signals[signal_handler.signal_name]
		except:
			pass
		else:
			try:
				handlers.remove(signal_handler)
			except:
				pass

	def signal_emit(self, signal_name, **kw):
		assert isinstance(signal_name, str)
		if signal_name not in self._signals:
			return True
		handlers = self._signals[signal_name]
		if not handlers:
			return True

		signal = Signal(origin=self, name=signal_name, **kw)

		# propagate
		for handler in tuple(handlers):
			if handler.active:
				try:
					if isinstance(handler.function, tuple):
						fnc = MethodType(*handler.function)
					else:
						fnc = handler.function
					if handler.pass_signal:
						fnc(signal)
					else:
						fnc()
					if signal.stopped:
						return False
				except ReferenceError:
					handlers.remove(handler)
		return True
