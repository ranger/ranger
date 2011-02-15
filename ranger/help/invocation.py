# Copyright (C) 2009, 2010  Roman Zimbelmann <romanz@lavabit.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
5. Ranger invocation

5.1. Command Line Arguments
5.2. Python Options


==============================================================================
5.1. Command Line Arguments

These options can be passed to ranger when starting it from the
command line.

--version
      Print the version and exit.

-h, --help
      Print a list of options and exit.

-d, --debug
      Activate the debug mode:  Whenever an error occurs, ranger
      will exit and print a full backtrace.  The default behaviour
      is to merely print the name of the exception in the statusbar/log
      and to try to keep running.

-c, --clean
      Activate the clean mode:  Ranger will not access or create any
      configuration files nor will it leave any traces on your system.
      This is useful when your configuration is broken, when you want
      to avoid clutter, etc.

--copy-config
      Create copies of the default configuration files in your local
      configuration directory.  Existing ones will not be overwritten.
      Possible values: all, apps, commands, keys, options, scope.

--fail-unless-cd
      Return the exit code 1 if ranger is used to run a file, for example
      with `ranger --fail-unless-cd filename`.  This can be useful for scripts.
      (This option used to be called --fail-if-run)

-r <dir>, --confdir=<dir>
      Define a different configuration directory.  The default is
      $HOME/.ranger.

-m <n>, --mode=<n>
      When a filename is supplied, make it run in mode <n> |2|

-f <flags>, --flags=<flags>
      When a filename is supplied, run it with the flags <flags> |2|

--choosefile=<target>
      Makes ranger act like a file chooser. When opneing a file, it will
      quit and write the name of the selected file to the filename specified
      as <target>. This file can be read in a script and used to open a
      certain file which has been chosen with ranger.

--choosedir=<target>
      Makes ranger act like a directory chooser. When ranger quits, it will
      write the name of the last visited directory to <target>

(Optional) Positional Argument
      The positional argument should be a path to the directory you
      want ranger to start in, or the file which you want to run.
      Only one positional argument is accepted as of now.

--
      Stop looking for options.  All following arguments are treated as
      positional arguments.

Examples:
      ranger episode1.avi
      ranger --debug /usr/bin
      ranger --confdir=~/.config/ranger --fail-unless-cd

See the README on how to integrate ranger with various external programs.


==============================================================================
5.2. Python Options

Ranger makes use of python optimize flags.  To use them, run ranger like this:
      PYTHONOPTIMIZE=1 ranger
An alternative is:
      python -O `which ranger`
Or you could change the first line of the ranger script and add -O/-OO.
The first way is the recommended one.  Of course you can make an alias or
a shell fuction to save typing.

Using PYTHONOPTIMIZE=1 (-O) will make python discard assertion statements.
Assertions are little pieces of code which are helpful for finding errors,
but unless you're touching sensitive parts of ranger, you may want to
disable them to save some computing power.

Using PYTHONOPTIMIZE=2 (-OO) will additionally discard any docstrings.
In ranger, most built-in documentation (F1/? keys) is implemented with
docstrings.  Use this option if you don't need the documentation.

Examples:
      PYTHONOPTIMIZE=1 ranger episode1.avi
      PYTHONOPTIMIZE=2 ranger --debug /usr/bin
      python -OO `which ranger` --confdir=~/.config/ranger --fail-unless-cd

Note: The author expected "-OO" to reduce the memory usage, but that
doesn't seem to happen.


==============================================================================
"""
# vim:tw=78:sw=8:sts=8:ts=8:ft=help
