require 'ncurses'

module Interface
	def self.keytable(key)
		case key
		when 12
			'<redraw>'
		when ?\n
			'<cr>'
		when ?\b, Ncurses::KEY_BACKSPACE
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
#		when ?\s
#			'<space>'
		when ?\t
			'<tab>'
		when 32
			' '
		when 0..127
			key.chr
		else
			log(key)
			''
		end
	end

#	def key c#{{{
#		case c
#		when 12
#			:redraw
#		when ?\n
#			:enter
#		when ?\b, Ncurses::KEY_BACKSPACE
#			:backspace
#		when 32
#			:space
#		when ?\t
#			:tab
#		when Ncurses::KEY_BTAB
#			:TAB
#		when ?\e
#			:escape
#		when 0..127
#			c
#		when Ncurses::KEY_F1..Ncurses::KEY_F30
#			('F' + (c-Ncurses::KEY_F1+1).to_s).to_sym
#		when Ncurses::KEY_HOME
#			:home
#		when Ncurses::KEY_END
#			:end
#		when Ncurses::KEY_RESIZE
#			:resize
#		when Ncurses::KEY_DC
#			:delete
#		when Ncurses::KEY_ENTER
#			?\n
#		when Ncurses::KEY_RIGHT
#			:right
#		when Ncurses::KEY_LEFT
#			:left
#		when Ncurses::KEY_UP
#			:up
#		when Ncurses::KEY_DOWN
#			:down
#		when Ncurses::KEY_NPAGE
#			:pagedown
#		when Ncurses::KEY_PPAGE
#			:pageup
#		when Ncurses::KEY_IC
#			:insert
#		else
##			c
#			:error
#		end
#	end#}}}

	def self.included(this)
		@@window = Ncurses.initscr
		starti
	end

	def starti
		@@screen = Ncurses.stdscr
		@@screen.keypad(true)
		Ncurses.start_color
		Ncurses.use_default_colors

		Ncurses.noecho
		Ncurses.curs_set 0
		Ncurses.halfdelay(10000)
		@@colortable = []
	end

	def closei
		Ncurses.echo
		Ncurses.cbreak
		Ncurses.curs_set 1
		Ncurses.endwin
	end

	def cleari
		Ncurses.mvaddstr(0, 0, ' ' * (lines * cols))
	end

	def geti
		Interface::keytable(Ncurses.getch)
	end

	def set_title(x)
		print "\e]2;#{x}\b"
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

	def color_at y, x=0, len=-1, fg=-1, bg=-1
		if OPTIONS['color']
			if y < 0 then y += Ncurses.LINES end
			Ncurses.mvchgat(y, x, len, 0, get_color(fg, bg), nil)
		end
	end

	def color_bold_at y, x=0, len=-1, fg=-1, bg=-1
		if OPTIONS['color']
			if y < 0 then y += Ncurses.LINES end
			Ncurses.mvchgat(y, x, len, Ncurses::A_BOLD, get_color(fg, bg), nil)
		end
	end

	def color_reverse_at y, x=0, len=-1, fg=-1, bg=-1
		if OPTIONS['color']
			if y < 0 then y += Ncurses.LINES end
			Ncurses.mvchgat(y, x, len, Ncurses::A_REVERSE, get_color(fg, bg), nil)
		else
			Ncurses.mvchgat(y, x, len, Ncurses::A_REVERSE, 0, nil)
		end
	end

#	runi(:command => String/Array, :wait=>false)
#	runi('ä́', 'b', 'c')
	def runi(hash, *args)
		wait = false
		if Array === hash
			command = hash
		elsif String === hash
			command = [hash, *args]
		else
			command = hash[:command] or return false
			wait = hash[:wait] if hash.has_key? :wait
		end

		closei

		system(*command)
		gets if wait

		starti
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
