module Fm
	# ALL combinations of multiple keys (without the last letter)
	# or regexps which match combinations need to be in here!
	COMBS = %w(
		g d y c Z rmdi t
		/[m`']/ /[f/!].*/
		/(cw|cd|mv).*/
		/m(k(d(i(r(.*)?)?)?)?)?/
		/r(e(n(a(m(e(.*)?)?)?)?)?)?/
	)

	# Create a regular expression which detects these combos
	ary = []
	for token in COMBS
		if token =~ /^\/(.*)\/$/
			ary << $1
		elsif token.size > 0
			ary << token.each_char.map {|t| "(?:#{t}" }.join +
				(')?' * (token.size - 1)) + ')'
		end
	end
	REGX = Regexp.new('^(?:' + ary.uniq.join('|') + ')$')

	def self.ignore_keys_for(t)
		@ignore_until = Time.now + t
	end

	def self.search(str, offset=0, backwards=false)
		rx = Regexp.new(str, Regexp::IGNORECASE)

		ary = @pwd.files.dup
		ary.wrap(@pwd.pos + offset)

		ary.reverse! if backwards

		for f in ary
			g = File.basename(f)
			if g =~ rx
				@pwd.pointed_file = f
				break
			end
		end
	end

	def self.hints(str)
		rx = Regexp.new(str, Regexp::IGNORECASE)

		ary = @pwd.files.dup
		ary.wrap(@pwd.pos)

		n = 0
		pointed = false
		for f in ary
			g = File.basename(f)
			if g =~ rx
				unless pointed
					@pwd.pointed_file = f
					pointed = true
				end
				n += 1
			end
		end

		return n
	end

	def self.remember_dir
		@memory["`"] = @memory["'"] = @pwd.path
	end

	def self.press(key)
		return if @ignore_until and Time.now < @ignore_until

		@ignore_until = nil

		case @buffer << key

		when '<redraw>'
			closei
			starti

		when 'j'
			if @pwd.size == 0
				@pwd.pos = 0
			elsif @pwd.pos >= @pwd.size - 1
				@pwd.pos = @pwd.size - 1
			else
				@pwd.pos += 1
			end

		when 's'
			closei
			system('clear')
			system('ls', '--color=auto', '--group-directories-first')
			system('bash')
			@pwd.refresh
			starti

		when 'J'
			(lines/2).times { press 'j' }

		when 'K'
			(lines/2).times { press 'k' }

		when 'cp', 'yy'
			@copy = [currentfile]

		when 'n'
			search(@search_string, 1)

		when 'x'
			fork {
				sleep 1
				Ncurses.ungetch(104)
			}

		when 'N'
			search(@search_string, 0, true)

		when 'fh'
			@buffer.clear
			press('h')

		when /^f(.+)$/
			str = $1
			if @buffer =~ /^(.*).<bs>$/
				@buffer = $1
			elsif str =~ /^\s?(.*)(L|;|<cr>|<esc>)$/
				@buffer = ''
				@search_string = $1
				press('l') if $2 == ';' or $2 == 'L'
			else
				test = hints(str)
				if test == 1
					@buffer = ''
					press('l')
					ignore_keys_for 0.5
				elsif test == 0
					@buffer = ''
					ignore_keys_for 1
				end
			end

		when /^\/(.+)$/
			str = $1
			if @buffer =~ /^(.*).<bs>$/
				@buffer = $1
			elsif str =~ /^\s?(.*)(L|;|<cr>|<esc>)$/
				@buffer = ''
				@search_string = $1
				press('l') if $2 == ';' or $2 == 'L'
			else
				search(str)
			end

		when /^mkdir(.*)$/
			str = $1
			if @buffer =~ /^(.*).<bs>$/
				@buffer = $1
			elsif str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					closei
					system('mkdir', $1)
					starti
					@pwd.refresh
				end
			end
			
		when /^!(.+)$/
			str = $1
			if @buffer =~ /^(.*).<bs>$/
				@buffer = $1
			elsif str =~ /^(\!?)(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $3 == '<cr>'
					closei
					system("bash", "-c", $2)
					gets unless $1.empty?
					starti
					@pwd.refresh
				end
			end

		when /^cd(.+)$/
			str = $1
			if @buffer =~ /^(.*).<bs>$/
				@buffer = $1
			elsif str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					remember_dir
					enter_dir_safely($1)
				end
			end

		when /^(?:mv|cw|rename)(.+)$/
			str = $1
			if @buffer =~ /^(.*).<bs>$/
				@buffer = $1
			elsif str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					closei
					system('mv', '-v', currentfile, $1)
					starti
					@pwd.refresh
				end
			end

		when 'th'
			OPTIONS['hidden'] ^= true
			@pwd.refresh

		when 'rmdir'
			cf = currentfile
			if cf and File.exists?(cf)
				if File.directory?(cf)
					system('rm', '-r', cf)
					@pwd.refresh
				end
			end

		when 'p'
			unless @copy.empty?
				closei
				system('cp','-v',*(@copy+[@pwd.path]))
				starti
				@pwd.refresh
			end

		when /^[`'](.)$/
			if dir = @memory[$1] and not @pwd.path == dir
				remember_dir
				enter_dir_safely(dir)
			end

		when /^m(.)$/
			@memory[$1] = @pwd.path

		when 'gg'
			@pwd.pos = 0

		when 'dd'
			new_path = move_to_trash(currentfile)
			@copy = [new_path] if new_path
			@pwd.refresh

		when 'dD'
			cf = currentfile
			if cf and File.exists?(cf)
				if File.directory?(cf)
					Dir.delete(cf) rescue nil
				else
					File.delete(cf) rescue nil
				end
				@pwd.refresh
			end

		when 'g0'
			remember_dir
			enter_dir('/')

		when 'gh'
			remember_dir
			enter_dir('~')

		when 'gu'
			remember_dir
			enter_dir('/usr')

		when 'ge'
			remember_dir
			enter_dir('/etc')

		when 'gm'
			remember_dir
			enter_dir('/media')

		when 'gt'
			remember_dir
			enter_dir('~/.trash')

		when 'G'
			@pwd.pos = @pwd.size - 1

		when 'k'
			@pwd.pos -= 1
			@pwd.pos = 0 if @pwd.pos < 0

		when '<bs>', 'h', 'H'
			enter_dir(@buffer=='H' ? '..' : @path[-2].path) unless @path.size == 1

		when 'E'
			cf = currentfile
			unless cf.nil? or enter_dir_safely(cf)
				closei
				system VI % cf
				starti
			end

		when '<cr>', 'l', ';', 'L'
			cf = currentfile
			unless cf.nil? or enter_dir_safely(cf)
				handler, wait = getfilehandler(currentfile)
				if handler
					closei
					system(handler)
					if @buffer == 'L'
						gets
					end
					starti
				end
			end

		when 'q', 'ZZ', "\004"
			exit

		end

		@buffer = '' unless @buffer == '' or @buffer =~ REGX
	end
end
