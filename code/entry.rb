require 'code/directory'

class Directory::Entry
	# Let's just cache every shit, because i don't want
	# to call File methods all the time

	BAD_TIME = Time.at(1)
	MIMETYPES = Marshal.load(File.read(
		File.join(MYDIR, 'data', 'mime.dat')))

	
	## wrapper
	def use() Use end
	module Use
		def self.no_handler()
			throw(:use, [nil, ''])
		end
		def self.method_missing(app, baseflags = '', *_)
			throw(:use, [app, baseflags])
		end
	end

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
		@ext = @ext.downcase
		if @ext == 'part'
			@name, @ext = @name.split_at_last_dot
			@ext = @ext.downcase
		end
		@size = 0
		@exists = false
		@rights = '--unread--'
		@readlink = ''
		@symlink = false
		@writable = false
		@stat = nil
		@infostring = ''
		@mimetype = nil
		@executable = false
		@type = :nonexistent
		@mtime = BAD_TIME
		@ctime = BAD_TIME
		@marked = false
	end

	attr_reader(*%w{
		basename mtime rights type path ext mimetype
		infostring readlink basename size ctime name
		stat
	})

	attr_accessor(:marked)
	
	def to_s() @path end
	def exists?() @exists end
	def marked?() @marked end
	def symlink?() @symlink end
	def socket?() @type == :socket end
	def video?() @video ||= @mimetype && @mimetype =~ /^video\// end
	def audio?() @sound ||= @mimetype && @mimetype =~ /^audio\// end
	def image?() @image ||= @mimetype && @mimetype =~ /^image\// end
	def broken_symlink?() @symlink and !@exists end
	def dir?() @type == :dir end
	def file?() @type == :file end
	def writable?() @writable end
	def executable?() @executable end
	alias movie? video?
	alias sound? audio?

	def displayname()
		@displayname ||= @basename.ascii_only_if(Option.ascii_only)
	end

	def handler()
		## get_handler has to be defined in another file
		return @handler if @handler
		@handler, @baseflags = catch(:use) do
			get_handler
		end
		@handler
	end

	def baseflags()
		return @baseflags if @baseflags
		@handler, @baseflags = catch(:use) do
			get_handler
		end
		@baseflags
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

		@exists = File.exists?( @path )
		if @exists
			@stat = File.stat( @path )
			@writable = @stat.writable?
			@symlink = File.symlink?( @path )
			if @symlink
				@readlink = File.readlink( @path )
			end
			if @stat.directory?
				@type = :dir
				begin
					sz = Dir.entries( @path ).size - 2
					@size = sz
				rescue
					sz = "?"
				end
				@infostring << "#{sz}"
			elsif @stat.socket?
				@type = :socket
			else
				@type = :file
				@mimetype = MIMETYPES[@ext]
				@size = @stat.size
				if @stat.size?
					@infostring << " #{File.size(@path).bytes 2}"
				else
					@infostring << ""
				end
			end
			@rights = @stat.modestr
			@executable = @stat.executable?
			@mtime = @stat.mtime
			@ctime = @stat.ctime

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
