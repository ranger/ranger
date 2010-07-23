# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
# This software is licensed under the GNU GPLv3; see COPYING for details.
import os
from os import sep, environ, makedirs

def _get_XDG_dir(varname, default_dirname):
	try:
		path = environ[varname]
	except:
		path = ''
	if path:
		result = sep.join([path, 'pithy'])
	else:
		result = sep.join([os.environ['HOME'], default_dirname, 'pithy'])
	try:
		makedirs(result)
	except:
		pass
	return result


def cache_dir():
	return _get_XDG_dir('XDG_CACHE_HOME', '.cache')


def conf_dir():
	return _get_XDG_dir('XDG_CONFIG_HOME', '.config')


def data_dir():
	return sep.join([os.path.dirname(__file__), 'data'])


def echo(text, filename):
	try:
		f = open(sep.join([cache_dir(), filename]), 'w')
	except:
		return False
	f.write(text)
	f.close()
