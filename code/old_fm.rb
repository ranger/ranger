class Directory
	def initialize(path)
		@path = path
		@pos = 0
		refresh
	end

	attr_reader(:path, :files)
	attr_accessor(:pos)

	def refresh()
		@files = Dir::glob(File::join(path, '*')).sort!
	end
	def self.current()
		Fm.current_dir()
	end
end

module Fm
	def self.initialize
		@key = ''
		@dirs = {}
		@current_dir = ''
		enter_dir(Dir.getwd)
	end

	def self.current_path() self.current_dir.path end

	attr_reader(:dirs, :current_dir)

#	{
#		"/" => [ 2,
#					 ["usr", "home", "root", "etc"] ],
#		 ...
#	}
	

	def self.getfilehandler(file)
		bn = File.basename(file)
		case bn
		when /\.(avi|mpg|flv)$/
			"mplayer #{file} >> /dev/null"
		when /\.(jpe?g|png)$/
			"feh '#{file}'"
		when /\.m3u$/
			"cmus-remote -c && cmus-remote -P #{file} && cmus-remote -C 'set play_library=false' && sleep 0.3 && cmus-remote -n"
		end
	end

	def self.enter_dir(dir)
		dir = File.expand_path(dir)
		olddirs = @dirs.dup
		@dirs = {}

		cur = 0
		got = ""
		ary = dir.split('/')
		if ary == []; ary = [''] end
		["", *ary].each do |folder|
			got = File.join(got, folder)
			cur = olddirs.has_key?(got) ? olddirs[got][0] : 0
			@dirs[got] = [cur, Dir.glob(File.join(got, '*')).sort]
		end

		# quick fix, sets the cursor correctly when entering ".."
		if @dirs.size < olddirs.size
			@dirs[@currentdir] = olddirs[@currentdir] 
			@dirs[got][0] = @dirs[got][1].index(@currentdir) || 0
		end

#		log @dirs

		@currentdir = got
#		@dirs[dir] = Dir[File.join(dir, '*')]
		Dir.chdir(got)
		
#		log(@dirs)
	end

	def self.cursor() @dirs[@currentdir][0] end
	def self.cursor=(x) @dirs[@currentdir][0] = x end

	def self.currentdir() @dirs[@currentdir][1] end

	def self.currentfile
		@dirs[@currentdir][1][@dirs[@currentdir][0] || 0]
	end

	def self.get_offset(dir, max)
		pos = dir[0]
		len = dir[1].size
		max -= 2
		if len <= max or pos < max/2
			return 0
		elsif pos > (len - max/2)
			return len - max
		else
			return pos - max/2
		end
	end

	def self.put_directory(c, d)
		l = 0
		unless d == nil
			offset = get_offset(d, lines)
			(lines - 1).times do |l|
				lpo = l + offset
				break if (f = d[1][lpo]) == nil

				if File.symlink?(f)
					color(3)
				elsif File.directory?(f)
					color(4)
				elsif File.executable?(f)
					color(2)
				else
					color(7)
				end
				puti l+1, c*@wid, File.basename(f).ljust(@wid-1)[0, @wid]
			end
		end

		column_clear(c, l)
	end

	def self.column_clear(n, from=0)
		(from -1).upto(lines) do |l|
			puti l+2, (n * @wid), ' ' * @wid
		end
	end

	def self.column_put_file(n, file)
		m = lines
		i = 0
		File.open(file, 'r') do |f|
			f.lines.each do |l|
				puti i+1, n * @wid, l.gsub("\t","   ")[0, @wid-1].ljust(@wid-1)
				i += 1
				break if i == m
			end
		end
		column_clear(n, i)
	end

	def self.draw
		color 7
		puti 0, 3, "pwd: #{@current_path}".ljust(cols)

		if @dirs.size == 1
			@temp = [nil, @dirs["/"]]
		else
			left = @dirs[@currentdir[0, @currentdir.rindex('/')]]
			left ||= @dirs['/']
			@temp = [left, @dirs[@currentdir]]
		end

		@wid = cols / 3
		f = currentfile
		begin
			if File.directory?(f)
				put_directory(2, [0, Dir.glob(File.join(f, '*')).sort])
			else
				column_put_file(2, currentfile)
			end
		rescue
			column_clear(2)
		end

		2.times do |c|
			put_directory(c, @temp[c])
		end

	
		movi(self.cursor + 1 - get_offset(@dirs[@currentdir], lines), @wid)
	end

	# ALL combinations of multiple keys have to be in the COMBS array.
	COMBS = %w(
		gg
	)
	def self.main_loop
		while true
			draw

			case @key << geti
			when 'j'
				self.cursor += 1
				self.cursor = currentdir.size - 1 if self.cursor >= currentdir.size

			when 'gg'
				self.cursor = 0

			when 'gh'
				enter_dir('~')

			when 'G'
				self.cursor = currentdir.size - 1

			when 'k'
				self.cursor -= 1
				self.cursor = 0 if self.cursor < 0

			when '<bs>', 'h'
				enter_dir('..') unless @dirs.size == 1

			when '<cr>', 'l'
				if File.directory?(currentfile || '')
					begin
						olddir = @currentdir
						enter_dir(currentfile)
					rescue Exception
						enter_dir olddir
					end
				else
					h = getfilehandler(currentfile)
					h and system(h)
				end

			when 'q'
				break
			end

			unless @key == '' or COMBS.select{ |x|
				x.size != @key.size and x.size > @key.size
			}.map{ |x|
				x[0, @key.size]
			}.include? @key
				@key = ''
			end
		end
	end
end

