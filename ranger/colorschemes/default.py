# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.

from __future__ import (absolute_import, division, print_function)

from ranger.gui.colorscheme import ColorScheme
from ranger.gui.color import (
    black, blue, cyan, green, magenta, red, yellow,
    bold, reverse, default
)


class Default(ColorScheme):
    progress_bar_color = blue

    colors = {
        'in_browser': {
            'default': {},
            'selected': {'attr': reverse},
            'empty': {'bg': red},
            'border': {'fg': default},
            'media': {
                'default': {'fg': magenta},
                'image': {'fg': yellow}
            },
            'container': {'fg': red},
            'directory': {'fg': blue, 'attr': bold},
            'executable': {'fg': green, 'attr': bold},
            'socket': {'fg': magenta, 'attr': bold},
            'fifo': {'fg': yellow},
            'device': {'fg': yellow, 'attr': bold},
            'link': {
                'default': {'fg': magenta},
                'good': {'fg': cyan}
            },
            'tag_marker': {'fg': red, 'attr': bold},
            'copied': {'fg': black, 'attr': bold},
            'main_column': {
                'selected': {'attr': bold},
                'marked': {'fg': yellow, 'attr': bold}
            },
            'badinfo': {'fg': magenta},
            'inactive_pane': {'fg': cyan}
        },
        'in_titlebar': {
            'default': {'attr': bold},
            'hostname': {
                'default': {'fg': green},
                'bad': {'fg': red}
            },
            'directory': {'fg': blue},
            'tab': {
                'default': {},
                'good': {'bg': green}
            },
            'link': {'fg': cyan}
        },
        'in_statusbar': {
            'default': {},
            'permissions': {
                'good': {'fg': cyan},
                'bad': {'fg': magenta}
            },
            'marked': {'fg': yellow, 'attr': bold | reverse},
            'frozen': {'fg': cyan, 'attr': bold | reverse},
            'message': {
                'default': {},
                'bad': {'fg': red, 'attr': bold},
            },
            'loaded': {'bg': progress_bar_color},
            'vcsinfo': {'fg': blue, 'attr': ~bold},
            'vcscommit': {'fg': yellow, 'attr': ~bold},
            'vcsdate': {'fg': cyan, 'attr': ~bold}
        },
        'text': {
            'default': {},
            'highlight': {'attr': reverse}
        },
        'in_taskview': {
            'default': {},
            'title': {'fg': blue},
            'selected': {'attr': reverse},
            'loaded': {
                'default': {'bg': progress_bar_color},
                'selected': {'fg': progress_bar_color}
            }
        },
        'vcsfile': {
            'default': {'attr': ~bold},
            'vcsconflict': {'fg': magenta},
            'vcsuntracked': {'fg': cyan},
            'vcschanged': {'fg': red},
            'vcsunknown': {'fg': red},
            'vcsstaged': {'fg': green},
            'vcssync': {'fg': green},
            'vcsignored': {}
        },
        'vcsremote': {
            'default': {'attr': ~bold},
            'vcssync': {'fg': green},
            'vcsnone': {'fg': green},
            'vcsbehind': {'fg': red},
            'vcsahead': {'fg': blue},
            'vcsdiverged': {'fg': magenta},
            'vcsunknown': {'fg': red}
        }
    }
