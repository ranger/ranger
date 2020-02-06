# This file is part of ranger, the console file manager.
# License: GNU GPL version 3, see the file "AUTHORS" for details.


def clipboards():
    """Return a list of commands that can be executed by subprocess.Popen
to copy some content into the system clipboard and proamry X
selection. The spawn processes will read the contents from the
standard input.

    >>> new_clipboard_contents = 'some string'
    >>> for command in clipboards():
            process = subprocess.Popen(command, universal_newlines=True,
                                       stdin=subprocess.PIPE)
            process.communicate(input=new_clipboard_contents)
"""
    from ranger.ext.get_executables import get_executables
    clipboard_managers = {
        'xclip': [
            ['xclip'],
            ['xclip', '-selection', 'clipboard'],
        ],
        'xsel': [
            ['xsel'],
            ['xsel', '-b'],
        ],
        'wl-copy': [
            ['wl-copy'],
        ],
        'pbcopy': [
            ['pbcopy'],
        ],
    }
    ordered_managers = ['pbcopy', 'wl-copy', 'xclip', 'xsel']
    executables = get_executables()
    for manager in ordered_managers:
        if manager in executables:
            return clipboard_managers[manager]
    return []
