class Directory
	BAD_TIME = Time.at(0)
	MOVIE_EXTENSIONS = %w(avi mpg mpeg mp4 mp5 ogv ogm wmv mkv flv fid vob div divx)
	class Entry #{{{
		# Let's just cache every shit, because i don't want
		# to call File methods all the time
		
		
		def initialize(dirname, basename=nil)
			if basename
				@path = File.join(dirname, basename)
				@dirname = dirname
				@basename = basename
			else
				@path = dirname
				@dirname = File.dirname(dirname)
				@basename = File.basename(dirname)
			end
			@name, @ext = @basename.split_at_last_dot
#			@ext = @basename.from_last('.') || ''
			@movie = MOVIE_EXTENSIONS.include?(@ext)
			@size = 0
			@exists = false
			@rights = '----------'
			@readlink = ''
			@symlink = false
			@writable = false
			@infostring = ''
			@executable = false
			@type = :nonexistent
			@mtime = BAD_TIME
			@ctime = BAD_TIME
			@marked = false
		end

		attr_reader *%w(
			basename mtime rights type path ext
			infostring readlink basename size ctime name
		)

		attr_accessor(:marked)
		
		def to_s() @path end
		def exists?() @exists end
		def marked?() @marked end
		def symlink?() @symlink end
		def movie?() @movie end
		def broken_symlink?() @symlink and !@exists end
		def dir?() @type == :dir end
		def file?() @type == :file end
		def writable?() @writable end
		def executable?() @executable end
		def mimetype()
			if @type == :dir
				nil
			else
				Fm::MIMETYPES[@ext]
			end
		end

		def delete!
			if @type == :dir
				Dir.delete(@path) rescue nil
			else
				File.delete(@path) rescue nil
			end
		end

		def refresh
			if File.exists?(@path)
				if File.ctime(@path) != @ctime
					get_data
				end
			else
				get_data
			end
		end

		def sh
			@path.sh
		end

		def in? path
			to_s[0, path.size] == path
		end

		def get_data
			@size = 0
			@infostring = ''

			@exists = File.exists?(@path)
			if @exists
				@writable = File.writable?(@path)
				@symlink = File.symlink?(@path)
				if @symlink
					@readlink = File.readlink(@path)
				end
				if File.directory?(@path)
					@type = :dir
					begin
						sz = Dir.entries(@path).size - 2
						@size = sz
					rescue
						sz = "?"
					end
					@infostring << "#{sz}"
				elsif File.socket?(@path)
					@type = :socket
				else
					@type = :file
					@size = File.size(@path)
					if File.size?(@path)
						@infostring << " #{File.size(@path).bytes 2}"
					else
						@infostring << ""
					end
				end
				@rights = File.modestr(@path)
				@executable = File.executable?(@path)
				@mtime = File.mtime(@path)
				@ctime = File.ctime(@path)

			else
				if File.symlink?(@path)
					@readlink = File.readlink(@path)
					@infostring = '->'
					@symlink = true
				else
					@symlink = false
				end
				@executable = false
				@writable = false
				@type = :nonexistent
				@rights = '----------'
				@mtime = BAD_TIME
				@ctime = BAD_TIME
			end
		end
	end #}}}

	PLACEHOLDER = Entry.new('/', 'placeholder')

	def initialize(path, allow_delay=false)
		@path = path
		@pos = 0
		@files = [PLACEHOLDER]
		@file_size = 0
		@pointed_file = nil
		@width = 1000
		@read = false
		@empty = true
		@scheduled = false

		refresh
	end

	def read_dir
		@mtime = File.mtime(@path)
		@files = Dir.new(@path).to_a
		if OPTIONS['hidden']
			@files -= ['.', '..', 'lost+found']
		else
			@files.reject!{|x| x[0] == ?. or x == 'lost+found'}
		end

		if @files.empty?
			@files = ['.']
		end

		@files_raw = @files.map{|bn| File.join(@path, bn)}
		@files.map!{|basename| Entry.new(@path, basename)}
	end

	attr_reader(:path, :files, :pos, :width, :files_raw,
					:file_size, :read)
	attr_accessor(:scheduled)

	def scheduled?() @scheduled end
	def read?() @read end

	def pos=(x)
#		if @files.size <= 1 or x < 0
#			x = 0
#		elsif x > @files.size
#			x = @files.size - 1
#		end
		@pos = x
		make_sure_cursor_is_in_range()
		@pointed_file = @files[x]
		resize
	end

	def recheck_stuff()
#		log "pointed file: #@pointed_file"
#		log @files_raw
#		log ""
		if test = @files_raw.index(@pointed_file)
#			log("if")
			@pos = test
		else
#			log("else")
			make_sure_cursor_is_in_range()
		end
	end

	def make_sure_cursor_is_in_range()
		if @files.size <= 1 or @pos < 0
			@pos = 0
		elsif @pos > @files.size
			@pos = @files.size - 1
		end
	end

	def find_file(x)
		x = File.basename(x)

		files.each_with_index do |file, i|
			if file.basename == x
				self.pos = i
			end
		end
	end

	def empty?()
		Dir.entries(@path).size <= 2
	end

	def restore()
		for f in @files
			f.marked = false
		end
	end

	def pointed_file=(x)
		if @files_raw.include?(x)
			@pointed_file = x
			@pos = @files_raw.index(x)
		else
			self.pos = 0
		end
		resize
	end

	def size() @files.size end

	def resize()
		pos = Fm.get_offset(self, lines)
		if @files.empty?
			@width = 0
		else
			@width = 0
			@files[pos, lines-2].each_with_index do |fn, ix|
				ix += pos
				sz = fn.basename.size + fn.infostring.size + 2
				@width = sz if @width < sz
			end
#			@width = @files[pos,lines-2].map{|x| File.basename(x).size}.max
		end
	end

	def get_file_info()
		@file_size = 0
		@files.each do |f|
			f.refresh
			@file_size += f.size if f.file?
		end
		@read = true
	end

#	def refresh()
#		@files = Dir.new(@path).to_a
#		if OPTIONS['hidden']
#			@files -= ['.', '..', 'lost+found']
#		else
#			@files.reject!{|x| x[0] == ?. or x == 'lost+found'}
#		end
#		if @files.empty?
#			@files = ['.']
#		end
#		@files.map!{|basename| Entry.new(@path, basename)}
#
#		if @pos >= @files.size
#			@pos = @files.size - 1
#		elsif @files.include?(@pointed_file)
#			@pos = @files.index(@pointed_file)
#		end
#	end
	def refresh(info=false)
		if File.mtime(@path) != @mtime
			read_dir
		end
		if info
			log("getting file info of #{@path}")
			get_file_info 
		end
		sort
	end

	def schedule()
		@scheduled = true
		Fm.schedule(self)
	end

	def refresh!()
		oldfile = @pointed_file
		read_dir
		get_file_info
		sort

		if @files.include? oldfile
			self.pointed_file = oldfile
		end
	end

	def sort_sub(x, y)
		case OPTIONS['sort']
		when :name
			x.basename <=> y.basename
		when :ext
			x.ext <=> y.ext
		when :type
			x.ext.filetype <=> y.ext.filetype
		when :size
			x.size <=> y.size
		when :ctime
			x.ctime <=> y.ctime
		when :mtime
			x.mtime <=> y.mtime
		else
			x.basename <=> y.basename
		end
	end

	def sort()
		@files = @files.sort {|x,y|
			if OPTIONS['dir_first']
				if x.dir?
					if y.dir? then sort_sub(x, y) else -1 end
				else
					if y.dir? then 1 else sort_sub(x, y) end
				end
			else
				sort_sub(x, y)
			end
		}
		@files.reverse! if OPTIONS['sort_reverse']
		@files_raw = @files.map{|x| x.to_s}
	end
end

