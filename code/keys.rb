# The default hotkeys are adjusted for the QWERTY layout.
# If you want to change them, please follow these steps:
#
#   1. if you map key X to key Y, make sure that key Y is not
#      mapped twice and remap the old mapping.
#   2. if you change key combinations, like "dd", please adjust
#      the key_combinations function. Search for the function
#      and you'll find detailed instructions.

module Fm
	def eval_keybuffer
		case @buffer

		## File Manipulation {{{

		when 'A'
			@buffer = "cw #{currentfile.name}"

		when /^mkdir(.*)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer.clear
				if $2 == '<cr>'
					Dir.mkdir($1) rescue lograise
					@pwd.schedule
				end
			end

		when /^touch(.*)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer.clear
				if $2 == '<cr>'
					File.open($1, 'a').close rescue lograise
					@pwd.schedule
				end
			end

		when 'P'
			for f in @copy
				File.symlink(f.path, File.expand_path(f.basename)) rescue lograise
			end

		when /^cm(r?)(\d{3})$/
			@buffer.clear
			chmod = FileUtils.method( $1.empty? ? :chmod : :chmod_R )
			chmod.call( $2.to_i( 8 ), *selection.map{|x| x.path} ) rescue lograise
			@pwd.refresh!

		when /^cm(r?)(.{9})$/
			@buffer.clear
			chmod = FileUtils.method( $1.empty? ? :chmod : :chmod_R )

			# extract octal mode number from $2
			mode = i = 0
			for part in $2.reverse.scan /.../
				factor = 8 ** i
				mode += factor * 1 if part.include? 'x'
				mode += factor * 2 if part.include? 'w'
				mode += factor * 4 if part.include? 'r'
				i += 1
			end
			chmod.call( mode, *selection.map{|x| x.path} ) rescue lograise
			@pwd.refresh!

		when /^co(r?)\s*(.*)\s*:\s*(.*)$/
			chown = FileUtils.method( $1.empty? ? :chown : :chown_R )
			user      = $2
			grp       = $3

			if grp =~ /^\s?(.*)(<cr>|<esc>)$/
				grp = $1
				@buffer.clear

				if $2 == '<cr>'
					chown.call( user.empty? ? nil : user,
					            grp.empty?  ? nil : grp,
									*selection.map{ |x| x.path } ) rescue lograise
				end
			end
			@pwd.refresh!


		## }}}

		## Destructive File Manipulation {{{

		## move to trash and copy new location
		when 'dd' + Option.confirm_string
			@copy = []
			@cut = false
			for file in selection
				new_path = move_to_trash(file)
				if new_path
					file = Directory::Entry.new(new_path)
					file.get_data
					@copy << file
				end
			end
			@marked.clear
			@pwd.refresh!

		## delete recursively forever
		when 'delete' + Option.confirm_string
			for file in selection
				FileUtils.remove_entry_secure(file.path) rescue lograise
			end
			@marked.clear
			@pwd.refresh!

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
			@marked.clear
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
				@buffer.clear
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

		when 'gR'
			remember_dir
			enter_dir( MYDIR )

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

		when '<cr>', '<right>', /^[li]$/i
			if currentfile.dir?
				enter_dir_safely(currentfile.path)
			else
				mode  = @buffer =~ /[LI]/ ?  1  : 0
				flags = @buffer =~ /[lL]/ ? 'a' : 'A'
				Action.run(RunContext.new(getfiles, mode, flags))
			end

		when 'n'
			quicksearch(1)

		when 'N'
			quicksearch(-1)

		when /^cd(.+)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				@buffer.clear
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

		when FIND_KEY_REGEXP
			Option.search_method = FIND_PROPERTIES[$1]
			search_reset!
			quicksearch(1)

		when 'fh'
			Option.search_method = :handler
			quicksearch(1)


		when /^f[rf](.+)$/
			str = $1
			Option.search_method = :regexp
			if str =~ /^\s?(.*)(L|;|<cr>|<esc>)$/
				@buffer.clear
				@search_string = $1 unless $1.empty?
				press('l') if $2 == ';' or $2 == 'L'
			else
				test = hints(str)
				if test == 1
					@buffer.clear
					press('l')
					ignore_keys_for 0.5
				elsif test == 0
					@buffer.clear
					ignore_keys_for 1
				end
			end

		when /^\/(.+)$/
			str = $1
			if str =~ /^\s?(.*)(L|;|<cr>|<esc>)$/
				@buffer.clear
				Option.search_method = :regexp
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

		when /^grep\s?(.*)$/
			if_enter_pressed($1) do |arg|
				files = @marked.empty? ? "*" : @marked.sh
				grep = 'grep --color=always --line-number'
				less = 'less'
				externally do
					system "#{grep} -e #{arg.sh} -r #{files} | #{less}"
				end
			end

		when /^gf\s?(.*)$/
			if_enter_pressed($1) do |arg|
				grep = 'grep --color=always'
				less = 'less'
				externally do
					system "find . | #{grep} #{arg} | #{less}"
				end
			end

		when 'du'
			externally do
				system "du --max-depth=1 -h | less"
			end

		when 'tar'
			externally do
				system('tar', 'cvvf', 'pack.tar', *selection.map{|x| x.basename})
				@pwd.refresh!
			end
			
		when /^!(.+)$/
			str = $1
			if str =~ /^(\!?)(.*)(<cr>|<esc>)$/
				@buffer.clear
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

		when /^r\s?(.*)$/
			if_enter_pressed($1) do |arg|
				@buffer.clear

				info, app = arg.split(":", 2)
				info =~ /(\d*)([adetw]*)/i
				mode, flags = $1, $2

				run_context = RunContext.new(getfiles, mode, flags, app)
				Action.run(run_context)
			end

		when "-", "="
			val = "2#{key=='-' ? '-' : '+'}"
			system("amixer", "-q", "set", "PCM", val, "unmute")

		## }}}

		## Control {{{

		when 'cp', 'yy'
			@copy = selection
			@cut = false

		when 'cut'
			@copy = selection
			@cut = true

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
			@marked.clear
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
			@marked.clear

		when /^F(.+)$/
			str = $1
			if str =~ /^\s?(.*)(<cr>|<esc>)$/
				if $2 == '<cr>'
					Directory.filter = $1
					@pwd.refresh!
				end
				@buffer.clear
			end

		## }}}

		## Options {{{

		when SORT_REGEXP
			how = SORT_KEYS[$1.downcase]
			log how

			@sort_time = Time.now
			Option.sort_reverse = $1.ord.between?(65, 90)
			Option.sort         = how  if how
			@path.each do |x| x.sort end
			update_pointers
#			@pwd.schedule

		when 'ea'
			edit File.join( MYDIR, 'data', 'apps.rb' )
			reload_types

		when 'et'
			edit File.join( MYDIR, 'data', 'types.rb' )
			reload_types

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

		when 'tu'
			Option.ascii_only ^= true

		when 'tc'
			Option.cd ^= true

		when 'td'
			Option.list_dir_first ^= true
			@pwd.schedule

		## }}}

		## Mouse {{{
		##
		## A left click is used for pointing at specific files and
		## moving to them.
		##
		## A right click is for navigation, moves back or forward
		## except if the right click is done in the current column,
		## where it will execute files.

		when Option.mouse && '<mouse>'
			log mouse.bstate
			if mouse.press1? or
				mouse.press3? or
				mouse.click1? or
				mouse.click3? or
				mouse.doubleclick1?

				left = ! (right = mouse.press3? or mouse.click3?)

				if mouse.y == 0
				elsif mouse.y >= CLI.lines - @bars.size - 1
				else
					boundaries = (0..3).map { |x| get_boundaries(x) }

					ranges = boundaries.map { |x| x.first .. x.first + x.last }

					case mouse.x
					when ranges[0]
						descend
						if left
							descend
							@pwd.pos = get_offset( @path[-1], lines ) + mouse.y - 1
						end
					when ranges[1]
						descend
						if left
							@pwd.pos = get_offset( @path[-1], lines ) + mouse.y - 1
						end
					when ranges[2]
						@pwd.pos = get_offset( @path[-1], lines ) + mouse.y - 1

						if right or mouse.doubleclick1?
							@buffer.clear
							if mouse.ctrl? then press('L') else press('l') end
						end
					when ranges[3]
						@buffer.clear
						if mouse.ctrl? then press('L') else press('l') end
						if left and currentfile.dir?
							@pwd.pos = get_offset( @path[-1], lines ) + mouse.y - 1
						end
					end
				end

			elsif mouse.press4?
				@buffer.clear
				press('k')

			elsif mouse.press5?
				@buffer.clear
				press('j')

			end

		## }}}

		end
	end

	# ALL key combinations have to be registered here, otherwise
	# they will not be recognized.
	def key_combinations
		return @@key_combinations if @@key_combinations

		# If your key combination looks like "cut",
		# you will have to enter the whole word minus the last letter.
		# that would be "cu".
		#
		# If it's more complicated, you will need to enter a custom regular
		# expression. Lets use the grep command for example.
		#
		# The regular expression would have to match "g", "gr", "gre", "grep"
		# and anything that starts with "grep", like "grep i want to find this"
		# This regexp would look like this: /g(r(e(p(.*)?)?)?)?/
		# 
		# Fore case insensitivity, please use /(?i:bla)/ rather than /bla/i
		# and do NOT use spaces or newlines inside a regexp

		@@key_combinations = %w[
			g y c Z cu f
			ter ta S e
			?? ?g ?f ?m ?l ?c ?o ?z ?s
			o m ` ' go

			um

			/:[^<]*/
			/[F/!].*/
			/(r|ff|fr|cw|cm|co|cd|mv|gf).*/
			/g(r(e(p(.*)?)?)?)?/
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
			elsif @buffer[-1] == ?>
				@buffer.slice!(/(<.*)?>$/)
			else
				@buffer.slice!(-1)
			end
		elsif key == '<c-u>'
			@buffer.clear
		else
			@buffer << key
		end

		eval_keybuffer

		@buffer.clear unless @buffer.empty? or @buffer =~ key_regexp
	end
	
	## go down 1 directory
	def descend
		Directory.filter = nil
		unless @path.size == 1
			enter_dir(@buffer=='H' ? '..' : @path[-2].path)
		end
	end

	def ignore_keys_for(t)
		@ignore_until = Time.now + t
	end

	def self.remember_dir
		@memory["`"] = @memory["'"] = @pwd.path
	end

	SORT_KEYS = {
		'n' => :name,
		'e' => :ext,
		't' => :type,
		's' => :size,
		'm' => :mtime,
		'c' => :ctime
	}

	SORT_REGEXP = /^S (?i: ( [#{ SORT_KEYS.keys * '|' }] )) $/x

	FINISHED = /^\s?(.*)(<cr>|<esc>)$/

	def if_enter_pressed( text, &block )
		return unless block_given?
		if text =~ FINISHED
			@buffer.clear
			if $2 == '<cr>'
				yield( $1 )
			end
		end
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
				ary << token.scan(/./).map {|t|
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

