# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import (
    black, blue, cyan, green, magenta, red, yellow,
    bold, reverse
)


class Default(ColorScheme):
    progress_bar_color = blue
    default_colors = (None, None, None)

    colors = {
        'in_browser': {
            'default': default_colors,
            'selected': (None, None, reverse),
            'empty': (None, red, None,),
            'border': default_colors,
            'media': {
                'default': (magenta, None, None),
                'image': (yellow, None, None)
            },
            'container': (red, None, None),
            'directory': (blue, None, bold),
            'executable': (green, None, bold),
            'socket': (magenta, None, bold),
            'fifo': (yellow, None, None),
            'device': (yellow, None, bold),
            'link': {
                'default': (magenta, None, None),
                'good': (cyan, None, None)
            },
            'tag_marker': (red, None, bold),
            'copied': (black, None, bold),
            'main_column': {
                'selected': (None, None, bold),
                'marked': (yellow, None, bold)
            },
            'badinfo': (magenta, None, None),
            'inactive_pane': (cyan, None, None)
        },
        'in_titlebar': {
            'default': (None, None, bold),
            'hostname': {
                'default': (green, None, None),
                'bad': (red, None, None)
            },
            'directory': (blue, None, None),
            'tab': {
                'default': default_colors,
                'good': (None, green, None)
            },
            'link': (cyan, None, None)
        },
        'in_statusbar': {
            'default': default_colors,
            'permissions': {
                'good': (cyan, None, None),
                'bad': (magenta, None, None)
            },
            'marked': (yellow, None, bold | reverse),
            'frozen': (cyan, None, bold | reverse),
            'message': {
                'default': default_colors,
                'bad': (red, None, bold),
            },
            'loaded': (None, progress_bar_color, None),
            'vcsinfo': (blue, None, ~bold),
            'vcscommit': (yellow, None, ~bold),
            'vcsdate': (cyan, None, ~bold)
        },
        'text': {
            'default': default_colors,
            'highlight': (None, None, reverse)
        },
        'in_taskview': {
            'default': default_colors,
            'title': (blue, None, None),
            'selected': (None, None, reverse),
            'loaded': {
                'default': (None, progress_bar_color, None),
                'selected': (progress_bar_color, None, None)
            }
        },
        'vcsfile': {
            'default': (None, None, ~bold),
            'vcsconflict': (magenta, None, None),
            'vcsuntracked': (cyan, None, None),
            'vcschanged': (red, None, None),
            'vcsunknown': (red, None, None),
            'vcsstaged': (green, None, None),
            'vcssync': (green, None, None),
            'vcsignored': default_colors
        },
        'vcsremote': {
            'default': (None, None, ~bold),
            'vcssync': (green, None, None),
            'vcsnone': (green, None, None),
            'vcsbehind': (red, None, None),
            'vcsahead': (blue, None, None),
            'vcsdiverged': (magenta, None, None),
            'vcsunknown': (red, None, None)
        }
    }
