class Bar
	def initialize( text = '' )
		@text = text
		@done = 0
		@thread = nil
		@update_proc = nil
		Fm.bar_add(self)
	end

	def kill(evil = true)
		Fm.bar_del(self)
		Fm.force_update

		@thread.kill
	end

	def update(&block)
		if block
			@update_proc = block
		elsif @update_proc
			@update_proc.call(self)
		end
	end

	attr_accessor :text, :done, :thread
end

class CopyBar < Bar
	def initialize( text = '' )
		super

		@update_proc = proc do |b|
			begin
				b.done = File.size(fname).to_f / finished
			rescue
				b.done = 0
			end
		end
	end
end

module Action
#	def self.get_all_files(path)
#		glob = Dir.new(path).to_a
#	end
	
	def self.make_a_bar_for_one(text, command)
		bar = CopyBar.new(test)

		finished = File.size(from[0]).to_f
		fname = File.join(to, File.basename(from[0]))

		bar.thread = Thread.new do
			begin
				system('ionice', '-c3', command, *(from + [to]))
			ensure
				bar.kill(false)
			end
		end
	end

	def self.copy(from, to)
#		log [from, to]

#		if String === from[0]
#			from[0] = Directory::Entry.new(from[0])
#		end

		if from.size == 1 and from[0].file?
			from = from[0]
			bar = Bar.new("Copying...")
			finished = from.size.to_f
			fname = File.join(to, from.basename)

			bar.update do |b|
				begin
					b.done = File.size(fname).to_f / finished
				rescue
					b.done = 0
				end
			end

			bar.thread = Thread.new do
				begin
					system('cp', from.to_s, to)
				ensure
					bar.kill(false)
				end
			end

		else
			bar = Bar.new("Copying...")
			from = from.dup
			from = [from] unless Array === from
			finished = Dir.number_of_files(*from.map{|x| x.to_s})
			count = 0

			bar.update do |b|
				begin
					b.done = count / finished
				rescue
					b.done = 0
				end
			end
			
			from.map!{|x| x.to_s}
			bar.thread = Thread.new do
				begin
					system('cp', '-r', *(from + [to.to_s]))
#					IO.popen("cp -vr #{from.join(' ')} #{to.sh}") do |f|
#					IO.popen(['cp', '-vr', *(from + [to])]) do |f|
#						count += 1 while f.gets =~ /' -> `/
#					end
				ensure
					bar.kill(false)
				end
			end
		end
	end

	def self.move(from, to)
#		log [from, to]
		
#		if String === from[0]
#			from[0] = Directory::Entry.new(from[0])
#		end

		if from.size == 1 and from[0].file?
			from = from[0]
			bar = Bar.new("Moving...")
			finished = from.size.to_f
			fname = File.join(to, from.basename)

			bar.update do |b|
				begin
					b.done = File.size(fname).to_f / finished
				rescue
					b.done = 0
				end
			end

			bar.thread = Thread.new do
				begin
					system('mv', from.to_s, to)
				ensure
					bar.kill(false)
				end
			end

		else
			bar = Bar.new("Moving...")
			from = from.dup
			from = [from] unless Array === from
			finished = Dir.number_of_files(*from.map{|x| x.to_s})
			count = 0

			bar.update do |b|
				begin
					b.done = count / finished
				rescue
					b.done = 0
				end
			end
			
			from.map!{|x| x.to_s}
			bar.thread = Thread.new do
				begin
					system('mv', *(from + [to.to_s]))
#					IO.popen("mv -v #{from.join(' ')} #{to.sh}") do |f|
#						count += 1 while f.gets =~ /' -> `/
#					end
				ensure
					bar.kill(false)
				end
			end
		end
	end
end

class Directory
	BAD_TIME = Time.at(0)
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

		attr_reader(:basename, :mtime, :rights, :type, :path,
					  :infostring, :readlink, :basename, :size, :ctime)

		attr_accessor(:marked)
		
		def to_s() @path end
		def exists?() @exists end
		def marked?() @marked end
		def symlink?() @symlink end
		def broken_symlink?() @symlink and !@exists end
		def dir?() @type == :dir end
		def file?() @type == :file end
		def writable?() @writable end
		def executable?() @executable end

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
			res = @path.dup
			res.gsub!('\\\\', "\000")
			res.gsub!(' ', '\\ ')
			res.gsub!('(', '\\(')
			res.gsub!('&', '\\&')
			res.gsub!(')', '\\)')
			res.gsub!('*', '\\*')
			res.gsub!('\'', '\\\'')
			res.gsub!('"', '\\"')
			res.gsub!("\000", '\\\\')
			return res
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

	attr_reader(:path, :files, :pos, :width, :files_raw, :file_size)

	def pos=(x)
		@pos = x
		@pointed_file = @files[x]
		resize
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
		Fm.schedule(self)
	end

	def refresh!()
		read_dir
		get_file_info
		sort
	end

	def sort_sub(x, y)
		case OPTIONS['sort']
		when :name
			x.basename <=> y.basename
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


class File
	MODES_HASH = {
		'0' => '---',
		'1' => '--x',
		'2' => '-w-',
		'3' => '-wx',
		'4' => 'r--',
		'5' => 'r-x',
		'6' => 'rw-',
		'7' => 'rwx'
	}
	def self.modestr(f)
		unless exists?(f)
			return '----------'
		end

		if symlink?(f)
			result = 'l'
		elsif directory?(f)
			result = 'd'
		else
			result = '-'
		end

		s = ("%o" % File.stat(f).mode)[-3..-1]
		for m in s.each_char
			result << MODES_HASH[m]
		end

		result
	end
end

class Dir
	def self.number_of_files(*dirs)
		n = 0
		dirs.each do |entry|
			if File.directory?(entry)
				n += 1 + number_of_files(*(Dir.new(entry).to_a - ['.', '..']).map\
												 {|x| File.join entry, x } )
			else
				n += 1
			end
		end
		return n
	end
end

class Numeric
	def limit(max, min = 0)
		self < min ? min : (self > max ? max : self)
	end

	def bytes space = true, n_round = 2
		n = 1024
		a = %w(B K M G T Y)

		i = 0
		flt = self.to_f

		while flt > n and i < a.length - 1
			flt /= n
			i += 1
		end

#		flt = flt.round(n_round)
		r = 10 ** n_round
		flt *= r
		flt = flt.round.to_f / r
		int = flt.to_i
		flt = int if int == flt

		return flt.to_s + (space ? ' ' + a[i] : a[i])
	end
end

class Array
	def wrap(n)
		n.times { push shift }
	end
end

class String
	def clear
		replace String.new
	end
	if RUBY_VERSION < '1.9'
		def ord
			self[0]
		end
	end

	def sh
		res = self.dup
		res.gsub!('\\\\', "\000")
		res.gsub!(' ', '\\ ')
		res.gsub!('(', '\\(')
		res.gsub!('&', '\\&')
		res.gsub!(')', '\\)')
		res.gsub!('*', '\\*')
		res.gsub!('\'', '\\\'')
		res.gsub!('"', '\\"')
		res.gsub!("\000", '\\\\')
		return res
	end

end

