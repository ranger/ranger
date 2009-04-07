
OPTIONS = {
	'hidden' => false,
}

module Fm
	def self.initialize
		@buffer = ''
		@pwd = ''
		@copy = []
		@ignore_until = nil
		@trash = File.expand_path('~/.trash')
		pwd = Dir.getwd

		@memory = {
			'`' => pwd,
			'\'' => pwd
		}

		@fmrc = File.expand_path('~/.fmrc')
		if (File.exists?(@fmrc))
			loaded = Marshal.load(File.read(@fmrc))
			if Hash === loaded
				@memory.update(loaded)
			end
		end

		@memory['0'] = pwd

		@dirs = Hash.new() do |hash, key|
			hash[key] = Directory.new(key)
		end

		@path = [@dirs['/']]
		enter_dir(Dir.pwd)
	end
	attr_reader(:dirs, :pwd)

	VI = "vi -c 'map h :quit<CR>' -c 'map q :quit<CR>' -c 'map H :unmap h<CR>:unmap H<CR>' %s"

	def self.dump
		remember_dir
		dumped = Marshal.dump(@memory)
		File.open(@fmrc, 'w') do |f|
			f.write(dumped)
		end
	end

	def self.rescue_me
		@buffer = ''
		sleep 0.2
	end

	def self.main_loop
		while true
			begin
				draw()
			rescue Interrupt
				rescue_me
			end
			begin
				press(geti)
			rescue Interrupt
				rescue_me
			end
		end
	end

	def self.current_path() @pwd.path end

	def self.enter_dir(dir)
		dir = File.expand_path(dir)

		oldpath = @path.dup

		# NOTE: @dirs[unknown] is not nil but Directory.new(unknown)
		@path = [@dirs['/']]
		unless dir == '/'
			dir.slice(0)
			accumulated = '/'
			for part in dir.split('/')
				unless part.empty?
					accumulated = File.join(accumulated, part)
					@path << @dirs[accumulated]
				end
			end
		end
		@pwd = @path.last
		set_title "fm: #{@pwd.path}"

		if @path.size < oldpath.size
			@pwd.pos = @pwd.files.index(oldpath.last.path) || 0
		end

		i = 0

		@path.each_with_index do |p, i|
			p.refresh
			unless i == @path.size - 1
				p.pointed_file = @path[i+1].path
			end
		end

		Dir.chdir(@pwd.path)
	end

	def self.currentfile
		@dirs[@currentdir][1][@dirs[@currentdir][0] || 0]
	end
	def self.currentfile() @pwd.files.at(@pwd.pos) end

	def self.get_offset(dir, max)
		pos = dir.pos
		len = dir.files.size
		max -= 2
		if len <= max or pos < max/2
			return 0
		elsif pos >= (len - max/2)
			return len - max
		else
			return pos - max/2
		end
	end

	COLUMNS = 4

	def self.get_boundaries(column)
		cols = Interface.cols # to cache
		case column
		when 0
			return 0, cols / 8 - 1
			
		when 1
			q = cols / 8
			return q, q

		when 2
			q = cols / 4
			w = @path.last.width.limit(cols/2, cols/8) + 1
			return q, w
			
		when 3
			l = cols / 4 + 1
			l += @path.last.width.limit(cols/2, cols/8)

			return l, cols - l
			
		end
	end

	def self.put_directory(c, d)
		l = 0
		if d
			infos = (c == COLUMNS - 2)
			left, wid = get_boundaries(c)

			offset = get_offset(d, lines)
			(lines - 1).times do |l|
				lpo = l + offset
				bg = -1
				break if (f = d.files[lpo]) == nil

				dir = false
				if File.symlink?(f)
					bld = true
					if File.exists?(f)
						clr = [6, bg]
					else
						clr = [1, bg]
					end
					dir = File.directory?(f)
				elsif File.directory?(f)
					bld = true
					dir = true
					clr = [4, bg]
				elsif File.executable?(f)
					bld = true
					clr = [2, bg]
				else
					bld = false
					clr = [7, bg]
				end

				fn = File.basename(f)
				if infos
					myinfo = " #{d.infos[lpo]}  "
					str = fn[0, wid-1].ljust(wid)
					if str.size > myinfo.size
						str[-myinfo.size..-1] = myinfo
						yes = true
					else
						yes = false
					end
					puti l+1, left, str
					if dir and yes
						args = l+1, left+wid-myinfo.size, myinfo.size, *clr
						color_bold_at(*args)
					end
				else
					puti l+1, left, fn[0, wid-1].ljust(wid+1)
				end

				args = l+1, left, fn.size.limit(wid-1), *clr

				if d.pos == lpo
					color_reverse_at(*args)
				else
					if bld then color_bold_at(*args) else color_at(*args) end
				end
			end
		end

		column_clear(c, l)
	end

	def self.column_clear(n, from=0)
		color(-1,-1)
		left, wid = get_boundaries(n)
		(from -1).upto(lines) do |l|
			puti l+2, left, ' ' * (wid)
		end
	end

	def self.column_put_file(n, file)
		m = lines - 2
		i = 0
		color 7
		bold false
		File.open(file, 'r') do |f|
			check = true
			left, wid = get_boundaries(n)
			f.lines.each do |l|
				if check
					check = false
					break unless l.each_char.all? {|x| x[0] > 0 and x[0] < 128}
				end
				puti i+1, left, l.gsub("\t","   ")[0, wid-1].ljust(wid)
				i += 1
				break if i == m
			end
		end
		column_clear(n, i)
	end

	def self.draw
		bold false
		@cur_y = get_boundaries(COLUMNS-2)[0]
		@pwd.get_file_infos

		s1 = "  "
		s2 = "#{@path.last.path}#{"/" unless @path.size == 1}"
		f = currentfile
		s3 = "#{f ? File.basename(f) : ''}"
		
		puti 0, (s1 + s2 + s3).ljust(cols)

		bg = -1
		color_at 0, 0, -1, 7, bg
		color_at 0, 0, s1.size, 7, bg
		color_at 0, s1.size, s2.size, 6, bg
		color_at 0, s1.size + s2.size, s3.size, 5, bg

		bold false

		f = currentfile
		begin
			if File.directory?(f)
				put_directory(3, @dirs[currentfile])
			else
				column_put_file(3, currentfile)
			end
		rescue
			column_clear(3)
		end

		pos_constant = @path.size - COLUMNS + 1

		(COLUMNS - 1).times do |c|
			pos = pos_constant + c

			if pos >= 0
				put_directory(c, @path[pos])
			else
				column_clear(c)
			end
		end

		bold false
		color -1, -1
		puti -1, "#@buffer    #{@pwd.pos+1},#{@pwd.size},#{@path.size}    ".rjust(cols)
		more = ''
		if File.symlink?(currentfile)
			more = "#{File.readlink(currentfile)}"
		end
		puti -1, "  #{Time.now.strftime("%H:%M:%S %a %b %d")}  #{File.modestr(currentfile)} #{more}"

		color_at -1, 23, 10, (File.writable?(currentfile) ? 6 : 5), -1
		if more
			color_at -1, 34, more.size, (File.exists?(currentfile) ? 6 : 1), -1
		end

		movi(@pwd.pos + 1 - get_offset(@pwd, lines), @cur_y)
	end

	def self.enter_dir_safely(dir)
		dir = File.expand_path(dir)
		if File.exists?(dir) and File.directory?(dir)
			olddir = @pwd.path
			begin
				enter_dir(dir)
				return true
			rescue
				enter_dir(olddir)
				return false
			end
		end
	end

	def self.move_to_trash!(fn)
		unless File.exists?(@trash)
			Dir.mkdir(@trash)
		end
		new_path = File.join(@trash, File.basename(fn))

		closei
		system('mv','-v', fn, new_path)
		starti

		return new_path
	end

	def self.in_trash?(fn)
		fn[0,@trash.size] == @trash
	end

	def self.move_to_trash(fn)
		if fn and File.exists?(fn)
			if File.directory?(fn)
				if !in_trash?(fn) and Dir.entries(fn).size > 2
					return move_to_trash!(fn)
				else
					Dir.rmdir(fn) rescue nil
				end
			elsif File.symlink?(fn)
				File.delete(fn)
			else
				if !in_trash?(fn) and File.size?(fn)
					return move_to_trash!(fn)
				else
					File.delete(fn)
				end
			end
		end
		return nil
	end
end

