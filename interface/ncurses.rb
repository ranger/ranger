require 'ncurses'

module Interface
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
# keep spaces as they are, makes more sense
#		when ?\s
#			'<space>'
		when Ncurses::KEY_BTAB
			'<s-tab>'
		when 9
			'<tab>'
		when 1..26 # CTRL + ...
			"<c-#{(key+96).chr}>"
		when 32..127
			key.chr
		else
			log(key)
			''
		end
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
		Ncurses.curs_set 0
		Ncurses.halfdelay(0)
		@@colortable = []
	end

	# Close the Interface
	def closei
		@@running = false
		Ncurses.echo
		Ncurses.cbreak
		Ncurses.curs_set 1
		Ncurses.endwin
	end

	def running?() @@running end

	def cleari
		Ncurses.mvaddstr(0, 0, ' ' * (lines * cols))
	end

	def geti
		Interface::keytable(Ncurses.getch)
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

	def color(fg = -1, bg = -1)
		if OPTIONS['color']
			Ncurses.color_set(get_color(fg,bg), nil)
		end
	end

	def color_at y, x=0, len=-1, fg=-1, bg=-1, attributes=0
		if OPTIONS['color']
			if y < 0 then y += Ncurses.LINES end
			Ncurses.mvchgat(y, x, len, attributes, get_color(fg, bg), nil)
		end
	end

	def color_bold_at y, x=0, len=-1, fg=-1, bg=-1
		color_at(y, x, len, fg, bg, attributes = Ncurses::A_BOLD)
	end

	def color_reverse_bold_at y, x=0, len=-1, fg=-1, bg=-1
		if OPTIONS['color']
			color_at(y, x, len, fg, bg, Ncurses::A_REVERSE | Ncurses::A_BOLD)
		else
			Ncurses.mvchgat(y, x, len, Ncurses::A_REVERSE | Ncurses::A_BOLD, 0, nil)
		end
	end
	alias color_bold_reverse_at color_reverse_bold_at

	def color_reverse_at y, x=0, len=-1, fg=-1, bg=-1
		if OPTIONS['color']
			color_at(y, x, len, fg, bg, Ncurses::A_REVERSE)
		else
			Ncurses.mvchgat(y, x, len, Ncurses::A_REVERSE, 0, nil)
		end
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

	def bold(b = true)
		if b
			Ncurses.attron(Ncurses::A_BOLD) 
		else
			Ncurses.attroff(Ncurses::A_BOLD) 
		end
	end

	def reverse(b = true)
		if b
			Ncurses.attron(Ncurses::A_REVERSE) 
		else
			Ncurses.attroff(Ncurses::A_REVERSE) 
		end
	end
end
