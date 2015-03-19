# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.
# Author: Joseph Tannhuber <sepp.tannhuber@yahoo.de>, 2013
# Solarized like colorscheme, similar to solarized-dircolors
# from https://github.com/seebi/dircolors-solarized.
# This is a modification of Roman Zimbelmann's default colorscheme.

from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import *

class Solarized(ColorScheme):
    progress_bar_color = 33

    def use(self, context):
        fg, bg, attr = default_colors

        if context.reset:
            return default_colors

        elif context.in_browser:
            fg = 244
            if context.selected:
                attr = reverse
            else:
                attr = normal
            if context.empty or context.error:
                fg = 235
                bg = 160
            if context.border:
                fg = default
            if context.media:
                if context.image:
                    fg = 136
                else:
                    fg = 166
            if context.container:
                fg = 61
            if context.directory:
                fg = 33
            elif context.executable and not \
                    any((context.media, context.container,
                        context.fifo, context.socket)):
                fg = 64
                attr |= bold
            if context.socket:
                fg = 136
                bg = 230
                attr |= bold
            if context.fifo:
                fg = 136
                bg = 230
                attr |= bold
            if context.device:
                fg = 244
                bg = 230
                attr |= bold
            if context.link:
                fg = context.good and 37 or 160
                attr |= bold
                if context.bad:
                    bg = 235
            if context.tag_marker and not context.selected:
                attr |= bold
                if fg in (red, magenta):
                    fg = white
                else:
                    fg = red
            if not context.selected and (context.cut or context.copied):
                fg = 234
                attr |= bold
            if context.main_column:
                if context.selected:
                    attr |= bold
                if context.marked:
                    attr |= bold
                    bg = 237
            if context.badinfo:
                if attr & reverse:
                    bg = magenta
                else:
                    fg = magenta

        elif context.in_titlebar:
            attr |= bold
            if context.hostname:
                fg = context.bad and 16 or 255
                if context.bad:
                    bg = 166
            elif context.directory:
                fg = 33
            elif context.tab:
                fg = context.good and 47 or 33
                bg = 239
            elif context.link:
                fg = cyan

        elif context.in_statusbar:
            if context.permissions:
                if context.good:
                    fg = 93
                elif context.bad:
                    fg = 160
                    bg = 235
            if context.marked:
                attr |= bold | reverse
                fg = 237
                bg = 47
            if context.message:
                if context.bad:
                    attr |= bold
                    fg = 160
                    bg = 235
            if context.loaded:
                bg = self.progress_bar_color

        if context.text:
            if context.highlight:
                attr |= reverse

        if context.in_taskview:
            if context.title:
                fg = 93

            if context.selected:
                attr |= reverse

            if context.loaded:
                if context.selected:
                    fg = self.progress_bar_color
                else:
                    bg = self.progress_bar_color

        return fg, bg, attr
