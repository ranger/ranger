"""
This is the default configuration file of ranger.
If you do any changes, make sure the import-line stays
intact and the type of the value stays the same.
"""

from ranger.api.options import *

colorscheme = colorschemes.default

max_history_size = 20
scroll_offset = 2
preview_files = True
flushinput = True

sort = 'basename'
reverse = False
directories_first = True

show_hidden = False
collapse_preview = True
autosave_bookmarks = True
update_title = True

show_cursor = False

hidden_filter = regexp(r'^\.|~$|\.(:?pyc|pyo|bak|swp)$')
