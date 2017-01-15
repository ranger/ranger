ranger v.1.8.1
==============

[![Build Status](https://travis-ci.org/ranger/ranger.svg?branch=master)](https://travis-ci.org/ranger/ranger)

ranger is a console file manager with VI key bindings.  It provides a
minimalistic and nice curses interface with a view on the directory hierarchy.
It ships with `rifle`, a file launcher that is good at automatically finding
out which program to use for what file type.

![screenshot](https://raw.githubusercontent.com/ranger/ranger-assets/master/screenshots/screenshot.png)

This file describes ranger and how to get it to run.  For instructions on the
usage, please read the man page.  See `HACKING.md` for development specific
information.

For configuration, check the files in `ranger/config/` or copy the
default config to `~/.config/ranger` with `ranger --copy-config`.

The `examples/` directory contains several scripts and plugins that demonstrate how
ranger can be extended or combined with other programs.  These files can be
found in the git repository or in `/usr/share/doc/ranger`.

A note to packagers: Versions meant for packaging are listed in the changelog
on the website.


About
-----
* Authors:     see `AUTHORS` file
* License:     GNU General Public License Version 3
* Website:     http://ranger.nongnu.org/
* Download:    http://ranger.nongnu.org/ranger-stable.tar.gz
* Bug reports: https://github.com/hut/ranger/issues
* git clone    http://git.sv.gnu.org/r/ranger.git


Design Goals
------------
* An easily maintainable file manager in a high level language
* A quick way to switch directories and browse the file system
* Keep it small but useful, do one thing and do it well
* Console based, with smooth integration into the unix shell


Features
--------
* UTF-8 Support  (if your python copy supports it)
* Multi-column display
* Preview of the selected file/directory
* Common file operations (create/chmod/copy/delete/...)
* Renaming multiple files at once
* VIM-like console and hotkeys
* Automatically determine file types and run them with correct programs
* Change the directory of your shell after exiting ranger
* Tabs, bookmarks, mouse support


Dependencies
------------
* Python (tested with version 2.6, 2.7, 3.1-3.5) with the `curses` module
  and (optionally) wide-unicode support.
* A pager (`less` by default)

Optional:

* The `file` program for determining file types
* The python module `chardet`, in case of encoding detection problems
* `sudo` to use the "run as root"-feature
* `w3m` for the `w3mimgdisplay` program to preview images

Optional, for enhanced file previews (with `scope.sh`):

* `img2txt` (from `caca-utils`) for ASCII-art image previews
* `highlight` or `pygmentize` for syntax highlighting of code
* `atool`, `acat`, `bsdtar` and/or `unrar` for previews of archives
* `lynx`, `w3m` or `elinks` for previews of html pages
* `pdftotext` for pdf previews
* `transmission-show` for viewing bit-torrent information
* `mediainfo` or `exiftool` for viewing information about media files
* `odt2txt` for OpenDocument text files (`odt`, `ods`, `odp` and `sxw`)


Installing
----------
Use the package manager of your operating system to install ranger.
Note that ranger can be started without installing by simply running `ranger.py`.

To install ranger manually:
```
sudo make install
```

This translates roughly to:
```
sudo python setup.py install --optimize=1 --record=install_log.txt
```

This also saves a list of all installed files to `install_log.txt`, which you can
use to uninstall ranger.


Getting Started
---------------
After starting ranger, you can use the Arrow Keys or `h` `j` `k` `l` to navigate, `Enter`
to open a file or type `Q` to quit.  The third column shows a preview of the
current file.  The second is the main column and the first shows the parent
directory.

Ranger can automatically copy default configuration files to `~/.config/ranger`
if you run it with the switch `--copy-config`. See `ranger --help` for a
description of that switch.  Also check `ranger/config/` for the default
configuration.
