# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function)

from ranger.gui.displayable import Displayable


class Widget(Displayable):
    """A class for classification of widgets."""

    vcsstatus_symb = {
        'conflict': (
            'X', ['vcsconflict']),
        'untracked': (
            '?', ['vcsuntracked']),
        'deleted': (
            '-', ['vcschanged']),
        'changed': (
            '+', ['vcschanged']),
        'staged': (
            '*', ['vcsstaged']),
        'ignored': (
            '·', ['vcsignored']),
        'sync': (
            '✓', ['vcssync']),
        'none': (
            ' ', []),
        'unknown': (
            '!', ['vcsunknown']),
    }

    vcsremotestatus_symb = {
        'diverged': (
            'Y', ['vcsdiverged']),
        'ahead': (
            '>', ['vcsahead']),
        'behind': (
            '<', ['vcsbehind']),
        'sync': (
            '=', ['vcssync']),
        'none': (
            '⌂', ['vcsnone']),
        'unknown': (
            '!', ['vcsunknown']),
    }

    ellipsis = {False: '~', True: '…'}
