# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

require 'ncurses'

module CLI
	@@mev = nil
	extend self

	def self.keytable(key)
		case key
		when 12
			'<redraw>'
		when ?\n
			'<cr>'
		when ?\b, Ncurses::KEY_BACKSPACE, 127
			'<bs>'
		when Ncurses::KEY_RIGHT
			'<right>'
		when Ncurses::KEY_LEFT
			'<left>'
		when Ncurses::KEY_UP
			'<up>'
		when Ncurses::KEY_DOWN
			'<down>'
		when ?\e
			'<esc>'
		when Ncurses::KEY_BTAB
			'<s-tab>'
		when 9
			'<tab>'
		when 1..26 # CTRL + ...
			"<c-#{(key+96).chr}>"
		when 32..127
			key.chr
		when Ncurses::KEY_MOUSE
			fetch_mouse_data
			'<mouse>'
		else
			''
		end
	end

	def fetch_mouse_data
		@@mev = MouseEvent.new
		Ncurses::getmouse(@@mev)
	end

	def mouse
		@@mev
	end

	def clear_keybuffer
		Ncurses.flushinp
	end

	def self.included(this)
		@@window = Ncurses.initscr
		starti
	end

	# (Re)Start the Interface
	def starti
		@@running = true
		@@screen = Ncurses.stdscr
		@@screen.keypad(true)
		Ncurses.start_color
		Ncurses.use_default_colors

		Ncurses.noecho
		Ncurses.ESCDELAY = 50
		Ncurses.curs_set 0
		Ncurses.halfdelay(200)
		@@colortable = []
	end

	MOUSE_MASK_ON = Ncurses::ALL_MOUSE_EVENTS | Ncurses::REPORT_MOUSE_POSITION
	MOUSE_MASK_OFF = 0

	def init_mouse( interval )
		Ncurses.mouseinterval( interval )
		Ncurses.mousemask( MOUSE_MASK_ON, [] )
	end

	def stop_mouse
		Ncurses.mousemask( MOUSE_MASK_OFF, [] )
	end

	def self.refresh
		Ncurses.refresh
	end

	# Close the Interface
	def closei
		@@running = false
		Ncurses.echo
		Ncurses.nocbreak
		Ncurses.curs_set 1
		Ncurses.endwin
	end

	def running?() @@running end

	def cleari
		Ncurses.mvaddstr(0, 0, ' ' * (lines * cols))
	end

	def geti
		CLI.keytable(Ncurses.getch)
	end

	def set_title(x)
		print "\e]2;#{x}\007"
	end

	def lines
		Ncurses.LINES
	end

	def cols
		Ncurses.COLS
	end

	def movi(y=0, x=0)
		y < 0 and y += lines
		Ncurses.move(y, x)
	end

	def puti *args
		case args.size
		when 1
			Ncurses.addstr(args[0].to_s)
		when 2
			if (y = args[0]) < 0 then y += Ncurses.LINES end
			Ncurses.mvaddstr(y, 0, args[1].to_s)
		when 3
			if (y = args[0]) < 0 then y += Ncurses.LINES end
			Ncurses.mvaddstr(y, args[1], args[2].to_s)
		end
	end

	def attr_set(fg=-1, bg=-1, attr = nil)
		fg, bg, attr = fg if fg.is_a? Array
		if attr
			Ncurses.attrset(attr | Ncurses.COLOR_PAIR(get_color(fg, bg)))
		else
			Ncurses.color_set(get_color(fg, bg), nil)
		end
	end

	def attr_at(y=0, x=0, len=-1, fg=-1, bg=-1, attr=0)
		fg, bg, attr = fg if fg.is_a? Array
		y += lines if y < 0
		x += cols if x < 0
		attr ||= 0

		Ncurses.mvchgat(y, x, len, attr, get_color(fg, bg), nil)
	end

	def get_color(fg, bg)
		n = bg+2 + 9*(fg+2)
		color = @@colortable[n]
		unless color
			# create a new pair
			size = @@colortable.reject{|x| x.nil? }.size + 1
			Ncurses::init_pair(size, fg, bg)
			color = @@colortable[n] = size
		end
		return color
	end

	class MouseEvent # {{{
		attr_accessor :id, :x,:y,:z, :bstate
		def press1?() 0 != @bstate & Ncurses::BUTTON1_PRESSED end
		def press2?() 0 != @bstate & Ncurses::BUTTON2_PRESSED end
		def press3?() 0 != @bstate & Ncurses::BUTTON3_PRESSED end
		def press4?() 0 != @bstate & Ncurses::BUTTON4_PRESSED end

		## this does not work. BUTTON5_* is not defined
		def press5?() 0 != @bstate & Ncurses::BUTTON5_PRESSED end

		## this is an EVIL fix but I don't know better
		def press5?() 0 != ( @bstate & 128 ) + ( @bstate & 134217728 ) end


		def release1?() 0 != @bstate & Ncurses::BUTTON1_RELEASED end
		def release2?() 0 != @bstate & Ncurses::BUTTON2_RELEASED end
		def release3?() 0 != @bstate & Ncurses::BUTTON3_RELEASED end
		def release4?() 0 != @bstate & Ncurses::BUTTON4_RELEASED end
#		def release5?() 0 != @bstate & Ncurses::BUTTON5_RELEASED end

		def click1?() 0 != @bstate & Ncurses::BUTTON1_CLICKED end
		def click2?() 0 != @bstate & Ncurses::BUTTON2_CLICKED end
		def click3?() 0 != @bstate & Ncurses::BUTTON3_CLICKED end
		def click4?() 0 != @bstate & Ncurses::BUTTON4_CLICKED end
#		def click5?() 0 != @bstate & Ncurses::BUTTON5_CLICKED end

		def doubleclick1?() 0 != @bstate & Ncurses::BUTTON1_DOUBLE_CLICKED end
		def doubleclick2?() 0 != @bstate & Ncurses::BUTTON2_DOUBLE_CLICKED end
		def doubleclick3?() 0 != @bstate & Ncurses::BUTTON3_DOUBLE_CLICKED end
		def doubleclick4?() 0 != @bstate & Ncurses::BUTTON4_DOUBLE_CLICKED end
#		def doubleclick5?() 0 != @bstate & Ncurses::BUTTON5_DOUBLE_CLICKED end

		def tripleclick1?() 0 != @bstate & Ncurses::BUTTON1_TRIPLE_CLICKED end
		def tripleclick2?() 0 != @bstate & Ncurses::BUTTON2_TRIPLE_CLICKED end
		def tripleclick3?() 0 != @bstate & Ncurses::BUTTON3_TRIPLE_CLICKED end
		def tripleclick4?() 0 != @bstate & Ncurses::BUTTON4_TRIPLE_CLICKED end
#		def tripleclick5?() 0 != @bstate & Ncurses::BUTTON5_TRIPLE_CLICKED end

		def alt?() 0 != @bstate & Ncurses::BUTTON_ALT end
		def shift?() 0 != @bstate & Ncurses::BUTTON_SHIFT end
		def ctrl?() 0 != @bstate & Ncurses::BUTTON_CTRL end

		## too many keys {{{
#		def press6?() 0 != @bstate & Ncurses::BUTTON6_PRESSED end
#		def press7?() 0 != @bstate & Ncurses::BUTTON7_PRESSED end
#		def press8?() 0 != @bstate & Ncurses::BUTTON8_PRESSED end
#		def press9?() 0 != @bstate & Ncurses::BUTTON9_PRESSED end
#		def release6?() 0 != @bstate & Ncurses::BUTTON6_RELEASED end
#		def release7?() 0 != @bstate & Ncurses::BUTTON7_RELEASED end
#		def release8?() 0 != @bstate & Ncurses::BUTTON8_RELEASED end
#		def release9?() 0 != @bstate & Ncurses::BUTTON9_RELEASED end
#		def click6?() 0 != @bstate & Ncurses::BUTTON6_CLICKED end
#		def click7?() 0 != @bstate & Ncurses::BUTTON7_CLICKED end
#		def click8?() 0 != @bstate & Ncurses::BUTTON8_CLICKED end
#		def click9?() 0 != @bstate & Ncurses::BUTTON9_CLICKED end
#		def doubleclick6?() 0 != @bstate & Ncurses::BUTTON6_DOUBLE_CLICKED end
#		def doubleclick7?() 0 != @bstate & Ncurses::BUTTON7_DOUBLE_CLICKED end
#		def doubleclick8?() 0 != @bstate & Ncurses::BUTTON8_DOUBLE_CLICKED end
#		def doubleclick9?() 0 != @bstate & Ncurses::BUTTON9_DOUBLE_CLICKED end
#		def tripleclick6?() 0 != @bstate & Ncurses::BUTTON6_TRIPLE_CLICKED end
#		def tripleclick7?() 0 != @bstate & Ncurses::BUTTON7_TRIPLE_CLICKED end
#		def tripleclick8?() 0 != @bstate & Ncurses::BUTTON8_TRIPLE_CLICKED end
#		def tripleclick9?() 0 != @bstate & Ncurses::BUTTON9_TRIPLE_CLICKED end
		# }}}
	end # }}}
end
