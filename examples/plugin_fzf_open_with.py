# pylint: disable=import-error, no-member, consider-using-with, consider-using-f-string
""" This plugin replaces the open_with menu with fzf. """

from __future__ import (absolute_import, division, print_function)

import logging
import subprocess

import ranger.core.actions

LOG = logging.getLogger(__name__)

# Save original function
DRAW_INFO_OLD = ranger.core.actions.Actions.draw_possible_programs
HOOK_INIT_OLD = ranger.api.hook_init


@classmethod
def draw_possible_programs_override(self):
    """
    Wrapper calling the original function, unsetting the draw_info array
    and invoking fzf instead.
    """

    # import pudb
    # pu.db

    DRAW_INFO_OLD(self)
    program_info = self.ui.browser.draw_info
    if len(program_info) < 1:
        return

    target = self.thistab.get_selection()[0]
    self.ui.browser.draw_info = []

    win_hei = self.ui.browser.hei + 2
    win_wid = self.ui.browser.wid
    fzf_menu_hei = min(win_hei, len(program_info) + 3)

    self.ui.win.move(win_hei - fzf_menu_hei, 0)
    self.ui.win.refresh()

    label = ' open %s with '
    label_pos = 3
    path_str = target.relative_path
    max_len = win_wid - (len(label) + label_pos)
    if len(path_str) > max_len:
        path_str = path_str[:max_len - 1] \
            + self.ui.browser.ellipsis[self.settings.unicode_ellipsis]

    process = subprocess.Popen(
        [
            'fzf', '--exact', '--accept-nth=1', '--height=%d' % fzf_menu_hei,
            '--reverse', '--info=hidden', '--no-sort', '--no-separator',
            '--bind', 'home:first', '--bind', 'end:last',
            '--border', '--border-label-pos=%d' % label_pos,
            '--border-label', label % path_str
        ], text=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, _ = process.communicate(input='\n'.join(program_info))

    # reset terminal cursor & mouse settings and redraw window
    self.ui.suspend()
    self.ui.initialize()

    if stdout:
        self.fm.execute_console('open_with %s' % stdout.strip())


def _log_function_address():
    LOG.info("%s hook_init ranger.core.actions.Actions.draw_possible_programs" % __name__
             + " = %s" % hex(id(ranger.core.actions.Actions.draw_possible_programs))
             + " draw_possible_programs_override = %s" % hex(id(draw_possible_programs_override)))


def hook_init(fm):
    """
    Hook into ranger init process.
    """

    # Remove subsequent open_with call from binding
    fm.execute_console('map r draw_possible_programs')

    _log_function_address()

    # FIXME: both ways don't make a difference in behaviour
    # ranger.core.actions.Actions.draw_possible_programs = draw_possible_programs_override
    ranger.core.actions.Actions.draw_possible_programs \
        = draw_possible_programs_override.__get__(None, ranger.core.actions.Actions)

    _log_function_address()

    return HOOK_INIT_OLD(fm)


ranger.api.hook_init = hook_init

# FIXME: this also doesn't work 🤔
_log_function_address()
ranger.core.actions.Actions.draw_possible_programs = draw_possible_programs_override
_log_function_address()
