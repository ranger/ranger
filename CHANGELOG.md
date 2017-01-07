This log documents changes between stable versions.

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
* Improved UI by separating file path in title bar with a space from the
  username/hostname for quick copy&pasting by shift+double-clicking on it.

# 2015-10-04: version 1.7.2
* Fixed file name arguments passed to `sxiv` and `feh` when using `:flat`
* Fixed removal of empty directories when using `:rename`
* Fixed free disk space display on Mac OS X
* Fixed `examples/vim_file_chooser` to work with gvim too
* Fixed some other rare crashes and bugs
* Fixed downward mouse wheel scrolling
* Fixed warning about regex splits being drawn in title bar since python3.5
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
