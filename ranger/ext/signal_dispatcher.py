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

	def signal_bind(self, signal_name, function, priority=0.5):
		assert isinstance(signal_name, str)
		try:
			handlers = self._signals[signal_name]
		except:
			handlers = self._signals[signal_name] = []
		nargs = function.__code__.co_argcount - hasattr(function, 'im_func')
		handler = SignalHandler(signal_name, function, priority, nargs > 0)
		handlers.append(handler)
		handlers.sort(key=lambda handler: -handler.priority)
		return handler

	def signal_unbind(self, signal_handler):
		try:
			handlers = self._signals[signal_handler.signal_name]
		except KeyError:
			pass
		else:
			handlers.remove(signal_handler)

	def signal_emit(self, signal_name, **kw):
		assert isinstance(signal_name, str)
		try:
			handlers = self._signals[signal_name]
		except:
			return
		if not handlers:
			return

		signal = Signal(origin=self, name=signal_name, **kw)

		for handler in handlers:  # propagate
			if handler.active:
				if handler.pass_signal:
					handler.function(signal)
				else:
					handler.function()
				if signal.stopped:
					return
