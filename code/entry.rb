require 'code/directory'

class Directory::Entry
	# Let's just cache every shit, because i don't want
	# to call File methods all the time

	BAD_TIME = Time.at(0)
	MOVIE_EXTENSIONS = %w(avi mpg mpeg mp4 mp5 ogv ogm wmv mkv flv fid vob div divx)
	
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

	attr_reader(*%w{
		basename mtime rights type path ext
		infostring readlink basename size ctime name
	})

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
				@readlink = File.readlink(@path) rescue nil
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
end
