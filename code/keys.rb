module Fm
	# ALL combinations of multiple keys (but without the last letter)
	# or regexps which match combinations need to be in here!
	COMBS = %w(
		g d y c Z delet cu
		t S ? ?g ?f

		/[m`']/ /[fF/!].*/
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
			ary << token.each_char.map {|t|
				if t == '?'
					t = '\?'
				end

				"(?:#{t}"
			}.join +
				(')?' * (token.size - 1)) + ')'
		end
	end
	REGX = Regexp.new('^(?:' + ary.uniq.join('|') + ')$')

	def self.ignore_keys_for(t)
		@ignore_until = Time.now + t
	end

	def self.search(str, offset=0, backwards=false)
		begin
			rx = Regexp.new(str, Regexp::IGNORECASE)
		rescue
			return false
		end

		ary = @pwd.files_raw.dup
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
		begin
			rx = Regexp.new(str, Regexp::IGNORECASE)
		rescue
			return false
		end

		ary = @pwd.files_raw.dup
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

		if key == '<bs>'
			if @buffer.empty?
				@buffer = key
			elsif @buffer == 'F'
				descend
			elsif @buffer[-1] == ?>
				@buffer.slice! /(<.*)?>$/
			else
				@buffer.slice! -1
			end
		else
			@buffer << key
		end

		case @buffer
		when '<redraw>'
			closei
			starti

		when 'j', '<down>'
			@pwd.pos += 1

		when 's'
			closei
			system('clear')
			ls = ['ls']
			ls << '--color=auto' if OPTIONS['color']
			ls << '--group-directories-first' if OPTIONS['color']
			system(*ls)
			system('bash')
			@pwd.schedule
			starti


		when /S(.)/
			OPTIONS['sort_reverse'] = $1.ord.between?(65, 90)

			case $1
			when 'n'
				OPTIONS['sort'] = :name
			when 's'
				OPTIONS['sort'] = :size
			when 'e'
				OPTIONS['sort'] = :extension
			when 'm'
				OPTIONS['sort'] = :mtime
			when 'c', 't'
				OPTIONS['sort'] = :ctime
			end
			@pwd.schedule

		when 'r', 'R'
			@pwd.refresh!

		when 'x'
			@bars.first.kill unless @bars.empty?

		when 'X'
			@bars.last.kill unless @bars.empty?

		when 'J'
			@pwd.pos += lines/2

		when 'K'
			@pwd.pos -= lines/2

		when 'cp', 'yy'
			if @marked.empty?
				@copy = [currentfile]
			else
				@copy = @marked.dup
			end
			@cut = false

		when 'cut'
			if @marked.empty?
				@copy = [currentfile]
			else
				@copy = @marked.dup
			end
			@cut = true

		when 'n'
			search(@search_string, 1)

		when 'N'
			search(@search_string, 0, true)

#		when 'fh'
#			@buffer.clear
#			press('h')

		when /^F(.+)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				if $2 == '<cr>'
					ascend
					@buffer = 'F'
				else
					@buffer.clear
					@search_string = $1
				end
			else
				test = hints(str)
				if test == 1
					if ascend
						@buffer.clear
					else
						@buffer = 'F'
					end
					ignore_keys_for 0.5
				elsif test == 0
					@buffer = 'F'
					ignore_keys_for 1
				end
			end

		when /^f(.+)$/
			str = $1
			if str =~ /^\s?(.*)(L|;|<cr>|<esc>)$/
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
			if str =~ /^\s?(.*)(L|;|<cr>|<esc>)$/
				@buffer = ''
				@search_string = $1
				press('l') if $2 == ';' or $2 == 'L'
			else
				search(str)
			end

		when /^mkdir(.*)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					closei
					system('mkdir', $1)
					starti
					@pwd.schedule
				end
			end
			
		when /^!(.+)$/
			str = $1
			if str =~ /^(\!?)(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $3 == '<cr>'
					closei
					system("bash", "-c", $2)
					gets unless $1.empty?
					starti
					@pwd.schedule
				end
			end

		when /^cd(.+)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					remember_dir
					enter_dir_safely($1)
				end
			end

		when /^(?:mv|cw|rename)(.+)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					Action.move(currentfile, $1)
				end
				@pwd.schedule
			end

		when 'tc'
			OPTIONS['color'] ^= true

		when 'tf'
			OPTIONS['filepreview'] ^= true

		when 'th'
			OPTIONS['hidden'] ^= true
			@pwd.refresh!

		when 'td'
			OPTIONS['dir_first'] ^= true
			@pwd.schedule

		when 'delete'
			files = @marked.empty? ? [currentfile] : @marked
			@marked = []
			for f in files
				if f and f.exists? and f.dir?
					system('rm', '-r', f.to_s)
					@pwd.schedule
				end
			end

		when 'p'
			if @cut
				Action.move(@copy, @pwd.path)
				@cut = false
			else
				Action.copy(@copy, @pwd.path)
			end

		when /^[`'](.)$/
			if dir = @memory[$1] and not @pwd.path == dir
				remember_dir
				enter_dir_safely(dir)
			end

		when '<tab>'
			if dir = @memory['`'] and not @pwd.path == dir
				remember_dir
				enter_dir_safely(dir)
			end
			

		when /^m(.)$/
			@memory[$1] = @pwd.path

		when ' '
			if currentfile.marked
				@marked.delete(currentfile)
				currentfile.marked = false
			else
				@marked << currentfile
				currentfile.marked = true
			end

			@pwd.pos += 1

		when 'v'
			@marked = []
			for file in @pwd.files
				if file.marked
					file.marked = false
				else
					file.marked = true
					@marked << file
				end
			end

		when 'V'
			for file in @marked
				file.marked = false
			end
			@marked = []


		when 'gg'
			@pwd.pos = 0

		when 'dd'
			new_path = move_to_trash(currentfile)
			if new_path
				new_path = Directory::Entry.new(new_path)
				new_path.get_data
				@copy = [new_path]
				@cut = false
			end
			@pwd.schedule

		when 'dD'
			cf = currentfile
			if cf and cf.exists?
				cf.delete!
				@pwd.schedule
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

		when 'k', '<up>'
			@pwd.pos -= 1

		when '<bs>', 'h', 'H', '<left>'
			descend

		when 'E'
			cf = currentfile.path
			unless cf.nil? or enter_dir_safely(cf)
				closei
				system VI % cf
				starti
			end

		when '<cr>', 'l', ';', 'L', '<right>'
			ascend(@buffer=='L')

		when 'q', 'ZZ', "\004"
			exit

		end

		@buffer = '' unless @buffer == '' or @buffer =~ REGX
	end
	
	def self.ascend(wait = false)
		cf = currentfile
		enter = enter_dir_safely(cf.path)
		unless cf.nil? or enter
			handler, wait = getfilehandler(currentfile)
			if handler
				closei
				log handler
				system(handler)
				gets if wait
				starti
				return true
			end
		end
		return false
	end

	def self.descend
		unless @path.size == 1
			enter_dir(@buffer=='H' ? '..' : @path[-2].path)
		end
	end
end

