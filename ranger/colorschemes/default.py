# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import (
    black, blue, cyan, green, magenta, red, white, yellow, default,
    normal, bold, reverse, dim, BRIGHT,
    default_colors,
)

def color(fg=-1, bg=-1, attr=0):
    return (fg, bg, attr)


def getkey(dictionary, key):
    keys = key.split('.')
    code = ''
    for i in dir():
        if eval(i) == dictionary:  # pylint: disable=eval-used
            code += i

    for k in keys:
        code += '["' + k + '"]'

    return eval(code)  # pylint: disable=eval-used


def has_key(dictionary, key):
    try:
        getkey(dictionary, key)
    except KeyError:
        return False
    return True


class Default(ColorScheme):
    progress_bar_color = None
    colors = {'progress_bar_color': blue}

    def _color(self, clrtup, valtup):
        clr = []
        if valtup[0] == default_colors[0]:
            clr.append(clrtup[0])
        else:
            clr.append(valtup[0])

        if valtup[1] == default_colors[1]:
            clr.append(clrtup[1])
        else:
            clr.append(valtup[1])

        if valtup[2] == default_colors[2]:
            clr.append(clrtup[2])
        else:
            clr.append(valtup[2])

        return (clr[0], clr[1], clr[2])

    def use(self, context):  # pylint: disable=too-many-branches, too-many-statements
        if self.progress_bar_color is not None:
            self.colors['progress_bar_color'] = self.progress_bar_color
        base_key = ''
        fg, bg, attr = default_colors

        if context.reset:
            if not has_key(self.colors, 'reset'):
                return default_colors
            return getkey(self.colors, 'reset')

        elif context.in_browser:
            base_key = 'browser.'
            if context.selected:
                if not has_key(self.colors, base_key + 'selected'):
                    attr = reverse
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'selected'))
            else:
                if not has_key(self.colors, base_key + 'default'):
                    attr = normal
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'default'))
            if context.empty:
                if not has_key(self.colors, base_key + 'empty'):
                    bg = red
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'empty'))
            if context.error:
                if not has_key(self.colors, base_key + 'error'):
                    bg = red
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'error'))
            if context.border:
                if not has_key(self.colors, base_key + 'border'):
                    fg = default
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'border'))
            if context.media:
                if context.image:
                    if not has_key(self.colors, base_key + 'media.image'):
                        fg = yellow
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'media.image'))
                else:
                    if not has_key(self.colors, base_key + 'default'):
                        fg = magenta
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'default'))
            if context.container:
                if not has_key(self.colors, base_key + 'container'):
                    fg = red
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'container'))
            if context.directory:
                if not has_key(self.colors, base_key + 'directory'):
                    attr |= bold
                    fg = blue
                    fg += BRIGHT
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'directory'))
            elif context.executable and not \
                    any((context.media, context.container,
                         context.fifo, context.socket)):
                if not has_key(self.colors, base_key + 'executable'):
                    attr |= bold
                    fg = green
                    fg += BRIGHT
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'executable'))
            if context.socket:
                if not has_key(self.colors, base_key + 'socket'):
                    attr |= bold
                    fg = magenta
                    fg += BRIGHT
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'socket'))
            if context.fifo:
                if not has_key(self.colors, base_key + 'fifo'):
                    fg = yellow
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'fifo'))
            if context.device:
                if not has_key(self.colors, base_key + 'fifo'):
                    fg = yellow
                    attr |= bold
                    fg += BRIGHT
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'fifo'))
            if context.link:
                if context.good:
                    if not has_key(self.colors, base_key + 'link.good'):
                        fg = cyan
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'link.good'))
                else:
                    if not has_key(self.colors, base_key + 'default'):
                        fg = magenta
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'default'))
            if context.tag_marker and not context.selected:
                if not has_key(self.colors, base_key + 'tag_marker'):
                    if fg in (red, magenta):
                        fg = white
                    else:
                        fg = red
                    fg += BRIGHT
                    attr |= bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'tag_marker'))
            if not context.selected and context.cut:
                if not has_key(self.colors, base_key + 'cut'):
                    attr |= bold
                    fg = black
                    fg += BRIGHT
                    # If the terminal doesn't support bright colors, use dim white
                    # instead of black.
                    if BRIGHT == 0:
                        attr |= dim
                        fg = white
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'cut'))
            if not context.selected and context.copied:
                if not has_key(self.colors, base_key + 'copied'):
                    attr |= bold
                    fg = black
                    fg += BRIGHT
                    # If the terminal doesn't support bright colors, use dim white
                    # instead of black.
                    if BRIGHT == 0:
                        attr |= dim
                        fg = white
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'copied'))
            if context.main_column:
                base_key = 'browser.main.'
                # Doubling up with BRIGHT here causes issues because it's
                # additive not idempotent.
                if context.selected:
                    if not has_key(self.colors, base_key + 'selected'):
                        attr |= bold
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'selected'))
                if context.marked:
                    if not has_key(self.colors, base_key + 'marked'):
                        attr |= bold
                        fg = yellow
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'marked'))
            base_key = 'browser.'
            if context.badinfo:
                if not has_key(self.colors, base_key + 'badinfo'):
                    if attr & reverse:
                        bg = magenta
                    else:
                        fg = magenta
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'badinfo'))
            if context.inactive_pane:
                if not has_key(self.colors, base_key + 'inactive'):
                    fg = cyan
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'inactive'))

        elif context.in_titlebar:
            base_key = 'titlebar.'

            if context.hostname:
                if context.bad:
                    if not has_key(self.colors, base_key + 'hostname.bad'):
                        fg = red
                        attr |= bold
                        fg += BRIGHT
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'hostname.bad'))
                else:
                    if not has_key(self.colors, base_key + 'hostname.default'):
                        fg = green
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'hostname.default'))
            elif context.directory:
                if not has_key(self.colors, base_key + 'directory'):
                    fg = blue
                    attr |= bold
                    fg += BRIGHT
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'directory'))
            elif context.tab:
                if context.good:
                    if not has_key(self.colors, base_key + 'tab.good'):
                        bg = green
                        attr |= bold
                        fg += BRIGHT
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'tab.good'))
            elif context.link:
                if not has_key(self.colors, base_key + 'link'):
                    fg = cyan
                    attr |= bold
                    fg += BRIGHT
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'link'))

        elif context.in_statusbar:
            base_key = 'statusbar.'

            if context.permissions:
                if context.good:
                    if not has_key(self.colors, base_key + 'permissions.good'):
                        fg = cyan
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'permissions.good'))
                elif context.bad:
                    if not has_key(self.colors, base_key + 'permissions.bad'):
                        fg = magenta
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'permissions.bad'))
            if context.marked:
                if not has_key(self.colors, base_key + 'marked'):
                    attr |= bold | reverse
                    fg = yellow
                    fg += BRIGHT
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'marked'))
            if context.frozen:
                if not has_key(self.colors, base_key + 'frozen'):
                    attr |= bold | reverse
                    fg = cyan
                    fg += BRIGHT
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'frozen'))
            if context.message:
                if context.bad:
                    if not has_key(self.colors, base_key + 'message'):
                        attr |= bold
                        fg = red
                        fg += BRIGHT
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'message'))
            if context.loaded:
                if not has_key(self.colors, base_key + 'loaded'):
                    bg = getkey(self.colors, 'progress_bar_color')
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'loaded'))
            if context.vcsinfo:
                if not has_key(self.colors, base_key + 'vcsinfo'):
                    fg = blue
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcsinfo'))
            if context.vcscommit:
                if not has_key(self.colors, base_key + 'vcscommit'):
                    fg = yellow
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcscommit'))
            if context.vcsdate:
                if not has_key(self.colors, base_key + 'vcsdate'):
                    fg = cyan
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcsdate'))

        if context.text:
            if context.highlight:
                if not has_key(self.colors, 'text.highlight'):
                    attr |= reverse
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'text.highlight'))

        if context.in_taskview:
            base_key = 'taskview'

            if context.title:
                if not has_key(self.colors, base_key + 'title'):
                    fg = blue
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'title'))

            if context.selected:
                if not has_key(self.colors, base_key + 'selected'):
                    attr |= reverse
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'selected'))

            if context.loaded:
                if context.selected:
                    if not has_key(self.colors, base_key + 'loaded.selected'):
                        fg = getkey(self.colors, 'progress_bar_color')
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'loaded.selected'))
                else:
                    if not has_key(self.colors, base_key + 'loaded.default'):
                        bg = getkey(self.colors, 'progress_bar_color')
                    else:
                        fg, bg, attr = self._color(
                            (fg, bg, attr), getkey(self.colors, base_key + 'loaded.default'))

        if context.vcsfile and not context.selected:
            base_key = 'vcsfile.'

            if context.vcsconflict:
                if not has_key(self.colors, base_key + 'vcsconflict'):
                    fg = magenta
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + ''))
            elif context.vcsuntracked:
                if not has_key(self.colors, base_key + 'vcsuntracked'):
                    fg = cyan
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + ''))
            elif context.vcschanged:
                if not has_key(self.colors, base_key + 'vcschanged'):
                    fg = red
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcschanged'))
            elif context.vcsunknown:
                if not has_key(self.colors, base_key + 'vcsunknown'):
                    fg = red
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcsunknown'))
            elif context.vcsstaged:
                if not has_key(self.colors, base_key + 'vcsstaged'):
                    fg = green
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + ''))
            elif context.vcssync:
                if not has_key(self.colors, base_key + 'vcssync'):
                    fg = green
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcssync'))
            elif context.vcsignored:
                if not has_key(self.colors, base_key + 'vcsignored'):
                    fg = default
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcsignored'))

        elif context.vcsremote and not context.selected:
            base_key = 'vcsremote'
            if context.vcssync:
                if not has_key(self.colors, base_key + 'vcssync'):
                    fg = green
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcssync'))
            if context.vcsnone:
                if not has_key(self.colors, base_key + 'vcsnone'):
                    fg = green
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcsnone'))
            elif context.vcsbehind:
                if not has_key(self.colors, base_key + 'vcsbehind'):
                    fg = red
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcsbehind'))
            elif context.vcsahead:
                if not has_key(self.colors, base_key + 'vcsahead'):
                    fg = blue
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcsahead'))
            elif context.vcsdiverged:
                if not has_key(self.colors, base_key + 'vcsdiverged'):
                    fg = magenta
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcsdiverged'))
            elif context.vcsunknown:
                if not has_key(self.colors, base_key + 'vcsunknown'):
                    fg = red
                    attr &= ~bold
                else:
                    fg, bg, attr = self._color(
                        (fg, bg, attr), getkey(self.colors, base_key + 'vcsunknown'))

        return fg, bg, attr
