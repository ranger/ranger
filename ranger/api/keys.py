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

import os
from curses import *
from curses.ascii import *
from inspect import getargspec, ismethod

from ranger import RANGERDIR
from ranger.gui.widgets import console_mode as cmode
from ranger.container.bookmarks import ALLOWED_KEYS as ALLOWED_BOOKMARK_KEYS

def make_abbreviations(command_list):
	def bind(*args, **keywords):
		if keywords:
			command_list.show(*args, **keywords)
		else:
			lastarg = args[-1]
			if hasattr(lastarg, '__call__'):
				# do the binding
				command_list.bind(lastarg, *args[:-1])
			else:
				# act as a decorator. eg:
				#    @bind('a')
				#    def do_stuff(arg):
				#       arg.fm.ui.do_stuff()
				#
				# is equivalent to:
				#    bind('a', lambda arg: arg.fm.ui.do_stuff())
				return lambda fnc: command_list.bind(fnc, *args)

	def show(*args, **keywords):
		command_list.show(*args, **keywords)

	def alias(*args):
		command_list.alias(*args)

	return bind, alias


class Wrapper(object):
	def __init__(self, firstattr):
		self.__firstattr__ = firstattr

	def __getattr__(self, attr):
		if attr.startswith('_'):
			raise AttributeError
		def wrapper(*real_args, **real_keywords):
			def function(command_argument):
				args, kws = real_args, real_keywords
				number = command_argument.n
				obj = getattr(command_argument, self.__firstattr__)
				fnc = getattr(obj, attr)
				if number is not None:
					args, kws = replace_narg(number, fnc, args, kws)
				return fnc(*args, **kws)
			return function
		return wrapper

# fm.enter_dir('~') is translated into lambda arg: arg.fm.enter_dir('~')
# this makes things like this possible:
# bind('gh', fm.enter_dir('~'))
#
# but NOT: (note the 2 dots)
# bind('H', fm.history.go(-1))
#
# for something like that, use the long version:
# bind('H', lambda arg: arg.fm.history.go(-1))
#
# If the method has an argument named "narg", pressing a number before
# the key will pass that number as the narg argument. If you want the
# same behaviour in a custom lambda function, you can write:
# bind('gg', fm.move_pointer(absolute=0))
# as:
# bind('gg', lambda arg: narg(arg.n, arg.fm.move_pointer, absolute=0))

fm = Wrapper('fm')
wdg = Wrapper('wdg')


NARG_KEYWORD = 'narg'

def narg(number_, function_, *args_, **keywords_):
	"""
	This applies the replace_narg function to the arguments and keywords
	and directly runs this function.

	Example:
	def foo(xyz, narg): return hash((xyz, narg))

	narg(50, foo, 123) == foo(123, narg=50)
	"""
	args, keywords = replace_narg(number_, function_, args_, keywords_)
	print(args, keywords)
	return function_(*args, **keywords)

def replace_narg(number, function, args, keywords):
	"""
	This function returns (args, keywords) with one little change:
	if <function> has a named argument called "narg", args and keywords
	will be modified so that the value of "narg" will be <number>.

	def foo(xyz, narg): pass

	replace_narg(666, foo, (), {'narg': 10, 'xyz': 5})
	=> (), {'narg': 666, 'xyz': 5}

	replace_narg(666, foo, (1, 2), {})
	=> (1, 666), {}
	"""
	argspec = getargspec(function).args
	if NARG_KEYWORD in argspec:
		try:
			# is narg in args?
			args = list(args)
			index = argspec.index(NARG_KEYWORD)
			if ismethod(function):
				index -= 1  # because of 'self'
			args[index] = number
		except (ValueError, IndexError):
			# is narg in keywords?
			keywords = dict(keywords)
			keywords[NARG_KEYWORD] = number
	return args, keywords
