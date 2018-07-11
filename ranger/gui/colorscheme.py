# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

"""Colorschemes define colors for specific contexts.

Generally, this works by passing a set of keywords (strings) to
the colorscheme.get() method to receive the tuple (fg, bg, attr).
fg, bg are the foreground and background colors and attr is the attribute.
The values are specified in ranger.gui.color.

A colorscheme must...

1. be inside either of these directories:
~/.config/ranger/colorschemes/
path/to/ranger/colorschemes/

2. be a subclass of ranger.gui.colorscheme.ColorScheme

3. implement a use(self, context) method which returns (fg, bg, attr).
context is a struct which contains all entries of CONTEXT_KEYS,
associated with either True or False.

Define which colorscheme in your settings (e.g. ~/.config/ranger/rc.conf):
set colorscheme yourschemename
"""

from __future__ import (absolute_import, division, print_function)

import os.path
from curses import color_pair

import ranger
from ranger.gui.color import get_color, normal, default_colors, reverse
from ranger.gui.context import Context
from ranger.core.main import allow_access_to_confdir
from ranger.ext.cached_function import cached_function
from ranger.ext.iter_tools import flatten


class ColorSchemeError(Exception):
    pass


class ColorScheme(object):
    """This is the class that colorschemes must inherit from.

    it defines the get() method, which returns the color tuple
    which fits to the given keys.
    """
    colors = {}

    fg, bg, attr = default_colors

    @cached_function
    def get(self, *keys):
        """Returns the (fg, bg, attr) for the given keys.

        Using this function rather than use() will cache all
        colors for faster access.
        """
        context = Context(keys)
        color = self.use(context)
        if len(color) != 3 or not all(isinstance(value, int) for value in color):
            raise ValueError("Bad Value from colorscheme.  Need "
                             "a tuple of (foreground_color, background_color, attribute).")
        return color

    @cached_function
    def get_attr(self, *keys):
        """Returns the curses attribute for the specified keys

        Ready to use for curses.setattr()
        """
        fg, bg, attr = self.get(*flatten(keys))
        return attr | color_pair(get_color(fg, bg))

    def color(self, tag, attr_and=False):
        if 'fg' in tag:
            self.fg = tag['fg']
        if 'bg' in tag:
            self.bg = tag['bg']
        if 'attr' in tag:
            if attr_and:
                self.attr &= tag['attr']
            else:
                self.attr |= tag['attr']

    def use(self, context):  # pylint: disable=too-many-branches,too-many-statements
        self.fg, self.bg, self.attr = default_colors

        if context.reset:
            return default_colors

        elif context.in_browser:
            tag = self.colors['in_browser']

            self.color(tag['default'])

            if context.selected:
                self.color(tag['selected'])
            else:
                self.color(default_colors)
            if context.empty or context.error:
                self.color(tag['empty'])
            if context.border:
                self.color(tag['border'])
            if context.media:
                if context.image:
                    self.color(tag['media']['image'])
                else:
                    self.color(tag['media']['default'])
            if context.container:
                self.color(tag['container'])
            if context.directory:
                self.color(tag['directory'])
            elif context.executable and not \
                    any((context.media, context.container,
                         context.fifo, context.socket)):
                self.color(tag['executable'])
            if context.socket:
                self.color(tag['socket'])
            if context.fifo:
                self.color(tag['fifo'])
            if context.device:
                self.color(tag['device'])
            if context.link:
                if context.good:
                    self.color(tag['link']['good'])
                else:
                    self.color(tag['link']['default'])
            if context.tag_marker and not context.selected:
                self.color(tag['tag_marker'])
            if (context.cut or context.copied) and not context.selected:
                self.color(tag['copied'])
            if context.main_column:
                if context.selected:
                    self.color(tag['main_column']['selected'])
                if context.marked:
                    self.color(tag['main_column']['marked'])
            if context.badinfo:
                self.color(tag['badinfo'])

            if context.inactive_pane:
                self.color(tag['inactive_pane'])

        elif context.in_titlebar:
            tag = self.colors['in_titlebar']

            self.color(tag['default'])

            if context.hostname:
                if context.bad:
                    self.color(tag['hostname']['bad'])
                else:
                    self.color(tag['hostname']['default'])
            elif context.directory:
                self.color(tag['directory'])
            elif context.tab:
                if context.good:
                    self.color(tag['tab']['good'])
                else:
                    self.color(tag['tab']['default'])
            elif context.link:
                self.color(tag['link'])

        elif context.in_statusbar:
            tag = self.colors['in_statusbar']

            self.color(tag['default'])

            if context.permissions:
                if context.good:
                    self.color(tag['permissions']['good'])
                elif context.bad:
                    self.color(tag['permissions']['bad'])
            if context.marked:
                self.color(tag['marked'])
            if context.frozen:
                self.color(tag['frozen'])
            if context.message:
                if context.bad:
                    self.color(tag['message']['bad'])
                else:
                    self.color(tag['message']['default'])
            if context.loaded:
                self.color(tag['loaded'])
            if context.vcsinfo:
                self.color(tag['vcsinfo'], attr_and=True)
            if context.vcscommit:
                self.color(tag['vcscommit'], attr_and=True)
            if context.vcsdate:
                self.color(tag['vcsdate'], attr_and=True)

        if context.text:
            tag = self.colors['text']
            if context.highlight:
                self.color(tag['highlight'])

        if context.in_taskview:
            tag = self.colors['in_taskview']
            if context.title:
                self.color(tag['title'])

            if context.selected:
                self.color(tag['selected'])

            if context.loaded:
                if context.selected:
                    self.color(tag['loaded']['selected'])
                else:
                    self.color(tag['loaded']['default'])

        if context.vcsfile and not context.selected:
            tag = self.colors['vcsfile']

            self.color(tag['default'])
            if context.vcsconflict:
                self.color(tag['vcsconflict'])
            elif context.vcsuntracked:
                self.color(tag['vcsuntracked'])
            elif context.vcschanged:
                self.color(tag['vcschanged'])
            elif context.vcsunknown:
                self.color(tag['vcsunknown'])
            elif context.vcsstaged:
                self.color(tag['vcsstaged'])
            elif context.vcssync:
                self.color(tag['vcssync'])
            elif context.vcsignored:
                self.color(tag['vcsignored'])

        elif context.vcsremote and not context.selected:
            tag = self.colors['vcsremote']

            self.color(tag['default'])
            if context.vcssync:
                self.color(tag['vcssync'])
            if context.vcsnone:
                self.color(tag['vcsnone'])
            elif context.vcsbehind:
                self.color(tag['vcsbehind'])
            elif context.vcsahead:
                self.color(tag['vcsahead'])
            elif context.vcsdiverged:
                self.color(tag['vcsdiverged'])
            elif context.vcsunknown:
                self.color(tag['vcsunknown'])

        if self.attr == reverse:
            self.attr = normal

        return self.fg, self.bg, self.attr


def _colorscheme_name_to_class(signal):  # pylint: disable=too-many-branches
    # Find the colorscheme.  First look in ~/.config/ranger/colorschemes,
    # then at RANGERDIR/colorschemes.  If the file contains a class
    # named Scheme, it is used.  Otherwise, an arbitrary other class
    # is picked.
    if isinstance(signal.value, ColorScheme):
        return

    if not signal.value:
        signal.value = 'default'

    scheme_name = signal.value
    usecustom = not ranger.args.clean

    def exists(colorscheme):
        return os.path.exists(colorscheme + '.py') or os.path.exists(colorscheme + '.pyc')

    def is_scheme(cls):
        try:
            return issubclass(cls, ColorScheme)
        except TypeError:
            return False

    # create ~/.config/ranger/colorschemes/__init__.py if it doesn't exist
    if usecustom:
        if os.path.exists(signal.fm.confpath('colorschemes')):
            initpy = signal.fm.confpath('colorschemes', '__init__.py')
            if not os.path.exists(initpy):
                open(initpy, 'a').close()

    if usecustom and \
            exists(signal.fm.confpath('colorschemes', scheme_name)):
        scheme_supermodule = 'colorschemes'
    elif exists(signal.fm.relpath('colorschemes', scheme_name)):
        scheme_supermodule = 'ranger.colorschemes'
        usecustom = False
    else:
        scheme_supermodule = None  # found no matching file.

    if scheme_supermodule is None:
        if signal.previous and isinstance(signal.previous, ColorScheme):
            signal.value = signal.previous
        else:
            signal.value = ColorScheme()
        raise ColorSchemeError("Cannot locate colorscheme `%s'" % scheme_name)
    else:
        if usecustom:
            allow_access_to_confdir(ranger.args.confdir, True)
        scheme_module = getattr(
            __import__(scheme_supermodule, globals(), locals(), [scheme_name], 0), scheme_name)
        if usecustom:
            allow_access_to_confdir(ranger.args.confdir, False)
        if hasattr(scheme_module, 'Scheme') and is_scheme(scheme_module.Scheme):
            signal.value = scheme_module.Scheme()
        else:
            for var in scheme_module.__dict__.values():
                if var != ColorScheme and is_scheme(var):
                    signal.value = var()
                    break
            else:
                raise ColorSchemeError("The module contains no valid colorscheme!")


def get_all_colorschemes(fm):
    colorschemes = set()
    # Load colorscheme names from main ranger/colorschemes dir
    for item in os.listdir(os.path.join(ranger.RANGERDIR, 'colorschemes')):
        if not item.startswith('__'):
            colorschemes.add(item.rsplit('.', 1)[0])
    # Load colorscheme names from ~/.config/ranger/colorschemes if dir exists
    confpath = fm.confpath('colorschemes')
    if os.path.isdir(confpath):
        for item in os.listdir(confpath):
            if not item.startswith('__'):
                colorschemes.add(item.rsplit('.', 1)[0])
    return list(sorted(colorschemes))
