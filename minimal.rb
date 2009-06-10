#!/usr/bin/ruby
require 'thread'
require 'ncurses'

Ncurses.initscr
Ncurses.cbreak

Thread.new { Thread.stop }
loop { Ncurses.getch }

