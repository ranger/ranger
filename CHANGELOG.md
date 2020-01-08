This log documents changes between stable versions.

# 2019-12-31: version 1.9.3
* Added Comic cbz/cbr previews
* Added DjVu previews
* Added Font previews
* Added Wayland support to rifle
* Added `imv` to rifle
* Added `paste_ext` command with new name collision behavior
* Added a `size_in_bytes` setting
* Added a new `%any_path` macro to simplify use of bookmarks in commands
* Added a new image previewing method using `ueberzug`
* Added archive previews
* Added filters for uniqueness and duplicates by hash to `filter_stack`
* Added generic openers to rifle, `xdg-open` for example
* Added line modes with human readable size information
* Added loading of plugins from local configuration directory
* Added previews for 3d models using `openscad`
* Added previews of MS Office documents
* Added scrolling in preview
* Added trash functionality to ranger, as alternative to deleting files
* Added zathura to rifle
* Changed `c/p/tunmap` to `unc/p/tmap` respectively, fixing them in the process
* Changed argument order for `tag_toggle`
* Fixed `chmod` behavior with `000` quantifier
* Fixed a crash involving `Ctrl+space`
* Fixed behavior of statusbar when resizing terminal window
* Fixed busyloop when ranger's STDIN was closed
* Fixed drawing of borders in st
* Fixed handling of macros for `chain`
* Fixed unicode decoding errors for previews
* Improved VCS integration by truncating long commit messages
* Improved `bulkrename` behavior when moving files to a non-existing directory
* Improved `bulkrename`'s handling of files with utf-16 surrogates in the name
* Improved behavior of `rename_append` for directories
* Improved configurability of syntax highlighting previews
* Improved coverage of unofficial MIME types, mostly audio formats
* Improved documentation of `multipane` viewmode
* Improved documentation of optional dependencies 
* Improved documentation on `copymap`
* Improved documentation on `tab_shift`
* Improved documentation on `w3m_offset`
* Improved example shell scripts
* Improved extensibility of image previewing methods using a registry
* Improved fuzzy tab completion
* Improved guessing of file encoding
* Improved handling of configuration and cache directories when using `--clean`
* Improved handling of invalid mtimes (Relevant for fuse mounts)
* Improved logging of file deletion
* Improved testing and CI setup
* Improved updating of tmux/screen window names
* Improved updating of window titles
* Improved validation of bookmarks
* Improved w3m preview method for terminals that aren't quite compatible


# 2018-09-09: version 1.9.2
* Added a `hint_collapse_threshold` setting
* Added a `traverse_backwards` command analogous to `traverse`
* Added a command to shift tabs
* Added a normal mode mapping to quickly enter the console and scroll through
  the history `C-p`
* Added a section to `scope.sh` for image previews of archives
* Added an avfs plugin
* Added an option to the move command to enable launching the selected file
  instead of the marked files
* Added filtering functionality inspired by dired's filter stack, `.n, .| ...`
* Added image preview method for Kitty
* Added option to disable the display of free space for high latency situations
* Added section to `scope.sh` for pdf previews with mutool
* Added several emacs/readline-inspired keybindings, `C-g` for `ESC`, `alt-f/b`
* Added systemwide `rc.conf` and `commands.py` in `/etc/ranger`
* Added the `%any_path` macro to allow bookmarks to be used with commands that
  need a path and are unaware of bookmarks
* Added versioning logic to include extra info in unreleased versions
* Change tab saving to save all tabs, not just the active tab
* Changed `draw_borders` setting to enable drawing only borders or seperators
* Changed behavior of positional arguments to the ranger command, if you
  specify a path to a file ranger will open with that file selected
* Changed the `tilde_in_titlebar` setting to influence the window titlebar too
* Changed the default colorscheme to work properly in terminals that don't
  equate bold and bright
* Fixed StopIteration errors
* Fixed embedded null errors
* Fixed issues reported by coverity scan
* Fixed running ranger as root on Mac OS
* Fixed unicode issue for python2
* Fixed w3m preview issues with black stripes
* Improved PEP8 adherence
* Improved VCS symbols
* Improved `--cmd` functionality
* Improved file encoding detection by using chardet if it's available
* Rifle's flag t should now work with more terminals than xterm and urxvt
* Update colorscheme documentation

# 2018-02-22: version 1.9.1
* Fixed the rifle config backwards compatibility (regression in 1.9.0)
* Fixed the POSIX compatibility of `Makefile`
* Fixed `--choosefile`, `--choosefiles` and `--choosedir` so they work
  with the process substitution (`>(...)` in Bash)
* Changed the default `gt` binding to `gp` due to a conflict
* Changed the help message for `--choosefile`, `--choosefiles` and
  `--choosedir` to avoid confusion
* Changed the behavior of `:reset` to reload the tags too
* Added `geeqie` to the default `rifle.conf`

# 2018-01-25: version 1.9.0
* Fixed memory leak in w3m image preview
* Fixed `Q` binding, map it to `quitall` instead of `quit!`
* Fixed `gR` binding
* Fixed custom linemode not being applied to files
* Fixed w3m image display invocation on OpenBSD
* Fixed broken pager after changing view mode with `~`
* Added reset of rifle.conf when pressing `<C-R>`
* Added image-based PDF previews to `scope.sh` (disabled by default)
* Added terminology-based image previews
* Added check for `$VISUAL` environment variable
* Added setting `iterm2_font_height` and `iterm2_font_width`
* Renamed setting `cd_tab_smart` to `cd_tab_fuzzy`
* Changed command for mercurial integration from `hg` to `chg`

# 2017-11-19: version 1.9.0b6
* Fixed crash when parsing corrupted history file
* Fixed tab completion with `cd -r ...`
* Fixed crash when previewing files encoded in little-endian UTF-16
* Fixed flicker in previewing symlinked images
* Fixed detection of location of scope.sh
* Fixed crash when running ranger from the directory containing its package
* Fixed cursor position after moving half a page down and back up
* Fixed handling of lines that are too long for the console
* Added `<F2>` binding to `:rename_append`
* Avoid dereferencing symlinked directory when starting ranger in one
* Added support for `file://` URIs as path arguments
* Added setting `save_tabs_on_exit`
* Added setting `cd_tab_case`, sets case sensitivity of `:cd` tab completion
* Added setting `cd_tab_smart`, allows fuzzy tab completion with `:cd`,
  for example, `:cd /u/lo/b<TAB>` expands to `:cd /usr/local/bin`
* Added setting `global_inode_type_filter` to show only directories when
  running ranger with the new option `--show-only-dirs`
* Added setting `save_backtick_bookmark`, e.g. for easier syncing of bookmarks
* Added setting `one_indexed` to start counting line numbers from 1
* Added rifle.conf entries to list/extract archives without atool
* Added `:yank` command for simplified definitions of `yn`, `yd` & `yp`
* Added `:narrow` command, which filters selected files
* Added setting `freeze_files`, bound to `F` key, to avoid reloading files
* Changed `:shell -p ...` to display stderr in pager

# 2017-02-19: version 1.9.0b5
* Fixed width calculation of multibyte characters in preview
* Fixed crash in iTerm2 preview with python 3.5

# 2017-02-10: version 1.9.0b1
* Fixed crash when using `Mi` on files without reading permissions
* Fixed natural sorting (`11.jpg` < `100.jpg`)
* Fixed loss of precision in timestamps when copying
* Fixed smart case matching in `:travel`
* Fixed automatically disabling `preview_script` when running as root
* Fixed crash on sshfs disconnect
* Fixed crash on missing `~/.config/ranger/history`
* Fixed crash when path not accessible during start-up
* Fixed automatic tmux title
* Fixed urxvt image previewing when running tmux
* Fixed macro expansion in aliased commands
* Fixed `hidden_filter` option when combined with `:flat`
* Fixed various other crashes
* Fixed error message that occasionally pops up when changing settings
* Introduced extensive linting to ensure code quality
* Added continuous integration.  Patches now require `make test` to pass.
* Added handling of arguments in "$PAGER" environment variable
* Added quote parsing for `:setlocal path=...`
* Added `ys` to copy the selection to clipboard
* Added setting `hostname_in_titlebar`
* Added setting `wrap_scroll` to wrap cursor around when scrolling
* Added example plugin `plugin_fasd_add.py`
* Added command `jump_non` to jump to the first non-directory file
* Added additional arguments to the command `:rename_append`
* Added key binding 'zz' as an alternative to 'zf'
* Added option `-c` to the `rifle` file opener command
* Added support for `$XDG_DATA_HOME`
* Avoid exiting ranger while copying.  Use `:quit!` to quit while copying.
* Improved scope.sh (better performance & readability)
* Improved logs handling by migrating to the python standard logging library (PR #725)
* Changed `ranger --choosefiles` to return all selected files in all paths
* Changed interpretation of commands: treat tabs as argument separators
* Changed `<C-n>` to open new tab in current directory rather than `$HOME`
* Changed `:quit!` to only close 1 tab.  Use `:quitall` to close all tabs.
* Removed backward compatibility for `options.py`, predecessor of `rc.conf`
* Automatically update bookmarks+tags when renaming them via ranger

# 2017-01-08: version 1.8.1
* Fixed `:scout` break due to incompatible change in python 3.6

# 2016-12-24: version 1.8.0
* scope.sh is now needed for the now fully scriptable image previews
* Overhaul of version control system integration, now with threads
* Fixed ranger not finding the location of w3mimgdisplay in most cases
* Fixed many minor bugs
* Added midnight-commander like multipane view, toggleable with `~` key.
  It displays the current directory of all the open tabs next to each other.
* Added autodetect for 256 color support in scope.sh source code preview
* Added macro `%confdir` that expands to `~/.config/ranger` by default
* Added possibility to toggle/cycle through options with `set <option_name>!`
* Added `Mm`/`Ms` key to enable the linemode showing modification time
* Added `yt`/`dt` keys to toggle whether file is in copy/cut buffer
* Added `line_numbers` setting showing absolute/relative line numbers
* Added `Alt-Left` and `Alt-Right` key bindings to move by words in console
* Added previews for libreoffice files with `odt2txt`
* Added `preview_images_method=urxvt` option for previewing images by changing
  the urxvt background (requires urxvt compiled with pixbuf support)
* Added `clear_filters_on_dir_change` option
* Added Travis-CI integration
* Changed `zi` key to toggle `preview_images` option
* Improved PEP8 compliance
* Improved documentation
* Improved UI by separating file path in titlebar with a space from the
  username/hostname for quick copy&pasting by shift+double-clicking on it.

# 2015-10-04: version 1.7.2
* Fixed file name arguments passed to `sxiv` and `feh` when using `:flat`
* Fixed removal of empty directories when using `:rename`
* Fixed free disk space display on Mac OS X
* Fixed `examples/vim_file_chooser` to work with gvim too
* Fixed some other rare crashes and bugs
* Fixed downward mouse wheel scrolling
* Fixed warning about regex splits being drawn in titlebar since python3.5
* Really fixed `S` key binding not working when SHELL=fish
* Improved `doc/cheatsheet.svg`
* Added some entries to rifle.conf
* Added key bindings `pO` and `pP` which work like `po` and `pp` but queue the
  operation in a first-in-first-out order.

# 2015-05-04: version 1.7.1
* Added `doc/cheatsheet.svg`
* Added `examples/rc_emacs.conf`, a config file adding emacs-like key bindings
* Added `env` keyword in rifle.conf
* Fixed `:bulkrename` command in python3
* Fixed `S` key binding not working when SHELL=fish

# 2015-04-13: version 1.7.0
* The default editor is now `vim` instead of `nano`
* Added automatic updates of tags when a file is renamed from within ranger
* Added `preview_images_method` which can be set to `iterm2` to use native
  iTerm2 image previews
* Added `:rename_append` command to rename files without the file extension
* Added `:linemode` command to change the way the files are displayed
  Try this out by pressing M followed by one of the suggested keys.
  New linemodes can be added with `ranger.api.register_linemode()`.
* Added `:filter_inode_type` command to only show directories, files or links
* Added `:meta` command for managing custom file metadata
* Added `:flat` command for displaying subdirectories
* Added `solarized` colorscheme
* Added generic ability to use scope.sh for image previews
* Added video previews in scope.sh
* Added option `sort_unicode` to sort according to unicode, not ASCII
* `:mkdir` can now create multiple directory levels (like `mkdir -p`)
* `:help` (key binding `?`) is now interactive
* `:find` (key binding `/`) is now case insensitive by default
* `ranger --copy-config=all` now copies a short sample commands.py rather than
  the full one, so that you can update ranger without having broken commands.
  The full commands.py is still copied to `~/.config/ranger/commands_full.py`.
* Fixed broken copying of symlinks

# 2013-05-24: Version 1.6.1
* Added support for version control systems, see:
  http://lists.nongnu.org/archive/html/ranger-users/2013-03/msg00007.html
* Added :scout command as a unified backend to :find, :search, etc
* Added `open_all_images` setting to remove the need for external scripts
  to handle opening of all images in a directory at once.
* Now previewing with `i` uses the whole available width.

# 2013-02-22: Version 1.6.0
* Overhauled all config files.  Please update them or use the --clean switch
* Added `examples/` directory to source code which contains sample programs or
  plugins that can be used together with ranger
* Added progress bars to copying, moving and directory loading processes
* Added feature to draw images inside the console using w3mimgdisplay (you need
  to add `set preview_images true` in rc.conf)
* Added a plugin system like in the program `anki`, i.e. place any python file
  into ~/.config/ranger/plugins/ and it will be imported by ranger
* Added a separate file launcher named `rifle` that is configured through
  rifle.conf and is installed as a standalone program.
  Using `ranger [filename]` from the shell for opening files is deprecated now,
  please use `rifle [filename]` instead.
* Added `uq` keybinding to undo closed tabs
* Added :setlocal command to change settings for specific directories only
* Added :travel command to move more quickly to your destination
* Added 256 color support for scope.sh
* Added a real yes/no prompt for :delete command
* Added settings: `confirm_on_delete`, `draw_progress_bar_in_status_bar`,
  `preview_images`, `status_bar_on_top`, `update_tmux_title`
* Added commands: `:mark_tag`, `:unmark_tag`
* Added BSD-friendly setsid implementation
* Added as-you-type filtering for `:filter` command
* Replaced `options.py` file by :set commands in rc.conf
* Replaced `apps.py` file with rifle.conf
* Improved `r` key to interface with rifle
* Rewritten `scope.sh` in POSIX shell
* Changed copying/moving code to work without GNU coreutils
* Changed key to untag files from `T` to `ut`
* Changed the flag `d` (for detached) to `f` (for fork) in program launcher
* Changed appearance of keybinding-hints and bookmarks
* Changed tabs with 4 spaces in the source code (see PEP 8)
* Removed ranger.core.environment class
* Removed settings: `colorscheme_overlay`, `draw_bookmark_borders`,
  `init_function`, `load_default_rc`
* Fixed zombie process apocalypse
* Fixed `draw_borders=true` in combination with `padding_right=false`

# 2012-08-10: Version 1.5.5
* Ensure that detached programs continue to run when ranger is killed

# 2012-05-03: Version 1.5.4
* Added exiftool to scope.sh by default
* Fixed a crash when entering a directory with a unicode name
* Speedup in `ranger.ext.get_executables`

# 2012-03-05: Version 1.5.3
* Added --selectfile option that selects a certain file on startup
* Added --list-tagged-files option
* Added --cmd option to run commands on startup
* Added --profile option for additional debug information on exit
* Added a visual mode (activate with `V`, deactivate with Esc)
* Added a reversed visual mode (activate with `uV`)
* Added `$RANGER_LEVEL` environment variable which ranger sets to `1` or higher
  so programs can know that they were spawned from ranger
* Added run flag `r` for running with root privileges (needs sudo)
* Added run flag `t` for running in a new terminal (as specified in $TERMCMD)
* Added :relink command to change destinations of symlinks
* Added `dc` binding for getting the cumulative size of a directory
* Added `autoupdate_cumulative_size` option
* Added `pht` binding to Paste Hardlinked subTrees (like cp -l)
* Improved sorting speed of signals (noticeable when caching many directories)
* Improved drawing speed
* Fixed unexpected behavior when displaying nonprintable characters
* Fixed :bulkrename to work with files starting with a minus sign
* Fixed RangerChooser example in man page
* Fixed crash when opening images with sxiv/feh by running `ranger <image>`

# 2011-10-23: Version 1.5.2
* Fixed graphical bug that appears in certain cases when drawing
  characters at the right edge.

# 2011-10-23: Version 1.5.1
* Added `fm.select_file(path)`
* Added --choosefiles option (like --choosefile, but chooses multiple files)
* Fixed --list-unused-keys
* Fixed Zombie processes
* Fixed handling of filenames with undecodable bytes (unicode surrogates)
* Fixed crashes due to incomplete loading of directories
* Fixed tab completion of the command `shell`
* Fixed `ot` and `oT` keys in rc.conf
* Fixed parsing of chained commands (like in the binding `om`)

# 2011-10-11: Version 1.5.0
* Full python3.2 compatibility
* Added new configuration file `rc.conf` which contains a list
  of commands that are executed on startup - mainly used for keybindings
* Added --list-unused-keys
* Added new program handlers to apps.py
* Added pop-up window for keychains and bookmarks
* Added `load_default_rc` option
* Fixed all known unicode issues
* Fixed crash when $TERM is unknown to the system
* Fixed scrolling in colored preview
* Changed the default `column_ratios` to 1/3/4 and sorting method to `natural`
* Changed :rename so it doesn't overwrite existing files
* Internal actions are now accessible as commands
* Replaced unittests by doctests
* Replaced integrated help with an extended man page and dynamic lists
  of keybindings, commands and settings.
* Removed `keys.py` configuration file in favor of `rc.conf`
* Removed `texas` colorscheme
* apps.py: Now able to define programs that only run with Xorg
* commands.py: Using parse(self.line) to parse the line is unnecessary now.
  parse(self.line).rest(n) is now written as self.rest(n).
  However, parse(self.line).chunk(n) has been renamed to self.arg(n).
* commands.py: parse(self.line) + X is now self.firstpart + X
* commands.py: New special attribute `resolve_macros` which decides whether
  strings like %f should be expanded to the name of the current file, etc.
* commands.py: New special attribute `escape_macros_for_shell` to toggle
  whether or not macros should be escaped, so you can use them in other
  commands than :shell, for example :edit %f
* Countless small fixes and improvements

# 2011-10-02: Version 1.4.4
* Added keys for chmod (like +ow for `chmod o+w`, etc)
* Added `c` flag for running files
* Added various key bindings
* Added wavpack and webm types to mime.types
* Added option `display_tags_in_all_columns`
* Added command.cancel method which is called when pressing ESC in console
* Added sorting and cycling by ctime and atime
* Added custom tags (press "x)
* Added bittorrent preview
* Fixed blocking when using interactive scripts in scope.sh
* Fixed issues with ALT key
* Fixed pager crash when trying to read non-readable file
* Forbid piping things into ranger
* Improved hints

# 2011-04-05: Version 1.4.3
* Fixed mimetype checking when invoking ranger with a filename
* Fixed loss of bookmarks when disk is full
* Minor improvements

# 2011-03-05: Version 1.4.2
* Added --choosefile and --choosedir flag
* Added use of bookmarks in tab completion of the :cd command
* Fixed bug with detached programs and python 3.2

# 2011-01-04: Version 1.4.1
* Fixed crash when preview failed under some circumstances
* Fixed graphical bug when pressing i

# 2010-12-22: Version 1.4.0
* Added option to use any external scripts for previews (see scope.sh)
* Added key: zv to toggle the use of the external script
* Added indicator for the used filter (type `zf`)
* Added option `padding_right` to remove whitespace if theres no preview
* Added command `:search_inc` for incremental search
* Added commands `:save_copy_buffer` and `:load_copy_buffer` to share
  the copied files between ranger instances
* Added mimeopen as a fallback if no useful application can be found
* Added natural sort, sorts 1foo before 10foo. (type `on`)
* Added keys: yp, yd and yb to copy path, dirname or basename to seleciton
* Let `open_with` use the selection, not just one file
* Run files with right mouse click
* Implemented copying via coreutils rather than internal python code
* Improved handling of unicode
* Some restructuration of the source code

# 2010-12-13: Version 1.2.3
* Enable binding to alt-keys
* Fixed memory leak in garbage collecting of old, unused directory objects
* Fixed python3 incompatibilities
* Fixed problems with identifying changes of files
* Fixed lazy lookup of some FSObject attributes

# 2010-10-10: Version 1.2.2
* Prevent currently used directories from being garbage collected
* Disable mouse buttons when console is open
* Fixed :cd command: Without arguments, cd's into $HOME
* Fixed bug which prevented pydoc to work on some config files
* Fixed some bugs in `snow` and `jungle` colorschemes
* Several other clean-ups and fixes

# 2010-09-16: Version 1.2.1
* Fixed yy/pp bug when yanking multiple directories

# 2010-09-13: Version 1.2.0
* !!! Changed the default configuration directory to ~/.config/ranger !!!
* Removed `Console Modes`, each old mode is now a simple command
* Disabled file previews by default if ranger is used by root
* Allow to jump to specific help sections by typing two numbers, e.g. 13?
* Added keys: da, dr, ya, yr for adding and removing files from copy buffer
* Added keys: gl and gL to resolve links, see 11?
* Added key: pL to create a relative symlink
* Added %<LETTER> and %<N><LETTER> macros for the console, see 33?
* Fixed ansi codes for colors in the pager
* Use the file ~/.mime.types for mime type detection
* Several clean-ups and fixes

# 2010-07-17: Version 1.1.2
* Fix crash when using scrollwheel to scroll down in some cases
* The command `ranger dir1 dir2 ...` opens multiple directories in tabs
* Removed pydoc html documentation by default, re-create it with `make doc`
* Minor fixes

# 2010-06-18: Version 1.1.1
* New install script, `setup.py`
* New flag for running programs: `w` (waits for enter press)
* Minor fixes

# 2010-06-09: Version 1.1.0
* Added a man page
* Tab support
* Improved directory loading performance
* Commands are definable in ~/.ranger/commands.py
* Case insensitive sorting (type zs)
* Better UTF support
* Possibility to turn off previews (zp and zP)
* Changing options with :set (e.g. `:set column_ratios=1,2,3,4`)
* Ask for confirmation when using :delete
* New invocation flag: --fail-unless-cd
* New hotkeys, commands, options.
* New syntax for ~/.ranger/keys.py
* Several user contributions
* And tons of general improvements
