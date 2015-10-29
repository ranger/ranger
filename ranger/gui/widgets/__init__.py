# -*- coding: utf-8 -*-

from ranger.gui.displayable import Displayable

class Widget(Displayable):
    """A class for classification of widgets."""

    vcsfilestatus_symb = {'conflict':  ('X', ["vcsconflict"]),
                  'untracked': ('+', ["vcschanged"]),
                  'deleted':   ('-', ["vcschanged"]),
                  'changed':   ('*', ["vcschanged"]),
                  'staged':    ('*', ["vcsstaged"]),
                  'ignored':   ('·', ["vcsignored"]),
                  'sync':      ('√', ["vcssync"]),
                  'none':      (' ', []),
                  'unknown':   ('?', ["vcsunknown"])}

    vcsremotestatus_symb = {'none':     (' ',  []),
                'sync':     ('=', ["vcssync"]),
                'behind':   ('<', ["vcsbehind"]),
                'ahead':    ('>', ["vcsahead"]),
                'diverged': ('Y', ["vcsdiverged"]),
                'unknown':  ('?', ["vcsunknown"])}

    ellipsis = { False: '~', True: '…' }
