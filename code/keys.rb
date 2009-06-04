module Fm
	# ALL combinations of multiple keys (but without the last letter)
	# or regexps which match combinations need to be in here!
	COMBS = %w(
		g d df y c Z delet cu
		ter ta S ? ?g ?f :q

		/[m`']/ /[fF/!].*/
		/[ri]\d*\w*[^ri]/
		/(cw|cd|mv).*/
		/b(l(o(c(k(.*)?)?)?)?)?/
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

	def self.find_newest()
		newest = nil
		for f in @pwd.files
			if newest.nil? or newest.ctime < f.ctime
				newest = f
			end
		end
		@pwd.pointed_file = newest.path
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
					log "point at #{f}"
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
		elsif key == '<c-u>'
			@buffer = ''
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


		when /^S(.)$/
			OPTIONS['sort_reverse'] = $1.ord.between?(65, 90)

			case $1
			when 'n'
				OPTIONS['sort'] = :name
			when 'e'
				OPTIONS['sort'] = :ext
			when 't'
				OPTIONS['sort'] = :type
			when 's'
				OPTIONS['sort'] = :size
			when 'm'
				OPTIONS['sort'] = :mtime
			when 'c'
				OPTIONS['sort'] = :ctime
			end
			@pwd.schedule

		when 'tar'
			closei
			system('tar', 'cvvf', 'pack.tar', *selection.map{|x| x.basename})
			@pwd.refresh!
			starti

		when 'R'
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
			@copy = selection
			@cut = false

		when 'cut'
			@copy = selection
			@cut = true

		when 'n'
			if @search_string.empty?
				find_newest
			else
				search(@search_string, 1)
			end

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

		when 'A'
			@buffer = "cw #{currentfile.name}"

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

		when /^block.*stop$/
			@buffer = ''
			
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

		when /^(mv|cw|rename)(.+)$/
			str = $2
			if $1 == 'mv'
				if str =~ /['`"]([\w\d])/
					if path = @memory[$1]
						str = ''
						@buffer.clear
						if File.exists?(path) and File.directory?(path)
							Action.move(selection, path)
						end
					end
				end
			end
			log str
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					files = selection
					if files.size == 1
						fn = $1
						log "!!! #{fn}"
						unless fn.include? '.'
							if ext = files.first.basename.from_last('.')
								fn << ".#{ext}"
							end
							log "??? #{ext}"
						end
						Action.move(files, fn)
						@pwd.refresh!
						@pwd.find_file(fn)
					else
						Action.move(files, $1)
						@pwd.refresh!
					end
				end
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
			files = selection
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
			@pwd.refresh!
			if @copy.size == 1
				@pwd.find_file(@copy[0].basename)
			end

		when /^[`'](.)$/
			if dir = @memory[$1] and not @pwd.path == dir
				remember_dir
				enter_dir_safely(dir)
			end

		when '<s-tab>'
			if dir = @memory['`'] and not @pwd.path == dir
				remember_dir
				enter_dir_safely(dir)
			end
			
		when '<tab>'
			if dir = @memory['9'] and dir != '/'
				unless @pwd.path == dir
					enter_dir_safely(dir)
				end
			elsif dir = @memory['`'] and not @pwd.path == dir
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

		when 'dD', 'dfd'
			cf = currentfile
			if cf and cf.exists?
				cf.delete!
				@pwd.schedule
			end

		when 'term'
			fork do exec 'x-terminal-emulator' end

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
			ascend(@buffer=='L', @buffer=='l')

		# a = run all
		# d or e = detach
		# t = run in a terminal
		# w = wait for <enter> after execution
		# capital letter inverts
		when /^[ri](\d*)([adetw]*)[ri]$/
			if $2.empty?
				f = @marked.empty?? currentfile : @marked.first
				flags = get_default_flags(f)
			else
				flags = $2
			end
			opt = OpenStruct.new
			opt.newway = true

			opt.mode = $1.to_i unless $1.empty?

			# Set options based on flags
			
			if flags =~ /a/
				opt.all = true
			end
			if flags =~ /[de]/
				opt.detach = true
			end
			if flags =~ /t/
				opt.new_term = true
				opt.detach = true
			end
			if flags =~ /w/
				opt.wait = true
			end

			if flags =~ /A/
				opt.all = false
			end
			if flags =~ /[DE]/
				opt.detach = false
			end
			if flags =~ /T/
				opt.new_term = false
			end
			if flags =~ /W/
				opt.wait = false
			end

			Action.run(opt.__table__)
		
#		when 'ra'
#			unless File.directory?(currentfile.path)
#				Action.run(:all=>true)
#			end

		when 'ZZ', '<c-d>', ':q<cr>', 'Q'
			exit
			
		when '<c-r>'
			Fm.boot_up

		when "-", "="
			val = "2#{key=='-' ? '-' : '+'}"
			system("amixer", "-q", "set", "PCM", val, "unmute")

		else
#			log key.ord

		end

		@buffer = '' unless @buffer == '' or @buffer =~ REGX
	end
	
	def self.ascend(wait = false, all=false)
		if all and !@marked.empty?
			closei
			system(*['mplayer', '-fs', *@marked.map{|x| x.path}])
			starti
			return true
		else
			cf = currentfile
			enter = enter_dir_safely(cf.path)
			unless enter
				return Action.run(:detach=>false)
			end
			return false
		end
	end

	def self.descend
		unless @path.size == 1
			enter_dir(@buffer=='H' ? '..' : @path[-2].path)
		end
	end
end

