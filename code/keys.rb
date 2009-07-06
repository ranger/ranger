module Fm
	# ALL combinations of multiple keys (but without the last letter)
	# or regexps which match combinations need to be in here!
	def key_combinations
		return @@key_combinations if @@key_combinations

		@@key_combinations = %w[
			g y c Z cu
			ter ta S ?? ?g ?f ?m ?l ?c ?o ?z
			o m ` ' go
			deleteI\ am   ddI\ am

			um

			/:[^<]*/
			/[fF/!].*/
			/r\d*\w*[^r]/
			/(cw|cd|mv).*/
			/b(l(o(c(k(.*)?)?)?)?)?/
			/m(k(d(i(r(.*)?)?)?)?)?/
			/t(o(u(c(h(.*)?)?)?)?)?/
			/r(e(n(a(m(e(.*)?)?)?)?)?)?/
		]

		need_confirmation = %w[
			delete
			dd
		]


		for str in need_confirmation
			@@key_combinations << (str + Option.confirm_string).chop
		end

		return @@key_combinations
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
				@buffer.slice!(/(<.*)?>$/)
			else
				@buffer.slice!(-1)
			end
		elsif key == '<c-u>'
			@buffer = ''
		else
			@buffer << key
		end

		case @buffer
		when 'cp', 'yy'
			@copy = selection
			@cut = false

		when 'cut'
			@copy = selection
			@cut = true

		when /^F(.+)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				if $2 == '<cr>'
					Directory.filter = $1
					@pwd.refresh!
				end
				@buffer.clear
			end

		when 'A'
			@buffer = "cw #{currentfile.name}"

		when /^mkdir(.*)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					begin
						Dir.mkdir($1)
					rescue
					end
					@pwd.schedule
				end
			end

		when /^touch(.*)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					begin
						File.open($1, 'a').close
					rescue
					end
					@pwd.schedule
				end
			end

		when /^block.*stop$/
			@buffer = ''

		when 'P'
			for f in @copy
				File.symlink(f.path, File.expand_path(f.basename))
			end

		## Destructive {{{

		when 'dd' + Option.confirm_string
			new_path = move_to_trash(currentfile)
			if new_path
				new_path = Directory::Entry.new(new_path)
				new_path.get_data
				@copy = [new_path]
				@cut = false
			end
			@pwd.schedule

		when 'dfd' + Option.confirm_string
			cf = currrentfile
			if cf and cf.exists?
				cf.delete!
				@pwd.schedule
			end

		when 'delete' + Option.confirm_string
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

		when /^o(.)$/
			if @memory[$1]
				Action.move(selection, @memory[$1])
			end
			@pwd.refresh!

		when /^(mv|cw|rename)(.+)$/
			str = $2
#			if $1 == 'mv'
#				if str =~ /['`"]([\w\d])/
#					if path = @memory[$1]
#						str = ''
#						@buffer.clear
#						if File.exists?(path) and File.directory?(path)
#							Action.move(selection, path)
#						end
#					end
#				end
#			end
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

		## }}}

		## Movement {{{

		## gX {{{
		when 'gg'
			@pwd.pos = 0

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

		when 'gn'
			remember_dir
			enter_dir('/mnt')

		when 'gt'
			remember_dir
			enter_dir('~/.trash')

		when 'gs'
			remember_dir
			enter_dir('/srv')
		## }}}

		when 'G'
			@pwd.pos = @pwd.size - 1

		when 'k', '<up>'
			@pwd.pos -= 1

		when 'j', '<down>'
			@pwd.pos += 1

		when '<bs>', 'h', 'H', '<left>'
			descend

		when 'J'
			@pwd.pos += lines/2

		when 'K'
			@pwd.pos -= lines/2

		when '<cr>', 'l', 'L', '<right>'
			if currentfile.dir?
				enter_dir_safely(currentfile.path)
			else
				mode = @buffer == 'L' ? 1 : 0
				Action.run(RunContext.new(getfiles, mode, 'a'))
			end

		when 'n'
			if @search_string.empty?
				find_newest
			else
				search(@search_string, 1)
			end

		when 'N'
			search(@search_string, 0, true)

		when /^cd(.+)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $2 == '<cr>'
					remember_dir
					enter_dir_safely($1)
				end
			end

		when /^(?:`|'|go)(.)$/
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

		when /^um(.)$/
			@memory.delete($1)

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

				press 'l' if $2 == ';' or $2 == 'L'
			else
				search(str)
			end

		## }}}

		## Launching applications {{{

		when 's'
			ls = ['ls']
			ls << '--color=auto' #if Option.color
			ls << '--group-directories-first' #if Option.color

			externally do
				system("clear; #{ls * ' '}; bash")
				@pwd.schedule
			end

		when 'tar'
			externally do
				system('tar', 'cvvf', 'pack.tar', *selection.map{|x| x.basename})
				@pwd.refresh!
			end
			
		when /^!(.+)$/
			str = $1
			if str =~ /^(\!?)(.*)(<cr>|<esc>)$/
				@buffer = ''
				if $3 == '<cr>'
					externally do
						system("bash", "-c", $2)
						Action.wait_for_enter unless $1.empty?
					end
					@pwd.schedule
				end
			end

		when 'term'
			fork do exec 'x-terminal-emulator' end

		when 'E'
			externally do
				Action.run(RunContext.new(getfiles, nil, nil, 'editor'))
			end

		when /^[ri](\d*)([adetw]*)[ri]$/
			run_context = RunContext.new(getfiles, $1, $2)
			Action.run(run_context)

		when "-", "="
			val = "2#{key=='-' ? '-' : '+'}"
			system("amixer", "-q", "set", "PCM", val, "unmute")

		## }}}

		## Control {{{

		when 'x'
			@bars.first.kill unless @bars.empty?

		when 'X'
			@bars.last.kill unless @bars.empty?

		when '<redraw>'
			externally

		when 'R'
			@pwd.refresh!

		when ' '
			if currentfile.marked
				@marked.delete(currentfile)
				currentfile.marked = false
			else
				@marked << currentfile
				currentfile.marked = true
			end

			@pwd.pos += 1

		
		when 'ZZ', '<c-d>', ':q<cr>', 'Q'
			exit

		when 'ZX'
			Option.cd ^= true
			exit

		when '<c-r>'
			Fm.boot_up

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

		## }}}

		## Options {{{

		when /^S(.)$/
			Option.sort_reverse = $1.ord.between?(65, 90)

			case $1
			when 'n'
				Option.sort = :name
			when 'e'
				Option.sort = :ext
			when 't'
				Option.sort = :type
			when 's'
				Option.sort = :size
			when 'm'
				Option.sort = :mtime
			when 'c'
				Option.sort = :ctime
			end
			@pwd.schedule

		when 't!'
			Option.confirm ^= true

		when 'tw'
			Option.wide_bar ^= true

		when 'tp'
			Option.preview ^= true

		when 'tf'
			Option.file_preview ^= true

		when 'th'
			Option.show_hidden ^= true
			@pwd.refresh!

		when 'tc'
			Option.cd ^= true

		when 'td'
			Option.dir_first ^= true
			@pwd.schedule

		## }}}

		end

		@buffer = '' unless @buffer == '' or @buffer =~ key_regexp
	end
	
	def self.descend
		Directory.filter = nil
		unless @path.size == 1
			enter_dir(@buffer=='H' ? '..' : @path[-2].path)
		end
	end

	def ignore_keys_for(t)
		@ignore_until = Time.now + t
	end

	def search(str, offset=0, backwards=false)
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

	def find_newest()
		newest = nil
		for f in @pwd.files
			if newest.nil? or newest.ctime < f.ctime
				newest = f
			end
		end
		@pwd.pointed_file = newest.path
	end

	def hints(str)
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


	def self.recalculate_key_combinations
		@@key_combinations = nil
		@@key_regexp = nil
	end
	recalculate_key_combinations

	def key_regexp
		return @@key_regexp if @@key_regexp

		# Create a regular expression which detects combos
		ary = []
		for token in key_combinations
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
		@@key_regexp = Regexp.new('^(?:' + ary.uniq.join('|') + ')$')
	end
end

