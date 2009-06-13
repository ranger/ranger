class RunContext
	## accessors {{{
	attr_accessor( *%w[
		all detach wait new_term
		files handlers paths
		mode
		exec
		multi
	])
	attr_reader( :flags )
	def flags=(x)
		assert x, Array, String

		if x.is_a? Array
			@flagstring = x.join('')
			@flags = x
		elsif x.is_a? String
			@flagstring = x
			@flags = x.split(//)
		end

		parse_flags
		return x
	end
	## }}}

	def initialize(files, mode=0, flags='')
		@mode = mode.to_i
		@files = files.dup
		self.flags = flags
		
		@files.reject! {|file|
			file.handler == nil or !file.exists?
		}
		@handlers = @files.map {|file| file.handler}
		@paths = @files.map {|file| file.path}
		@handler = @handlers.first

		@multi = (@files.size > 1 and @handlers.uniq.size == 1)

		@exec = Application.send(@handler, self)
	end

	def has_flag? x
		if x.is_a? Regexp
			@flagstring =~ x
		elsif x.is_a? String
			@flags.include? x
		else
			false
		end
	end

	def parse_flags
		@all = @detach = @new_term = @wait = false

		## Positive flags
		if has_flag? 'a'
			@all = true
		end
		if has_flag? /[de]/
			@detach = true
		end
		if has_flag? 't'
			@new_term = true
			@detach = true
		end
		if has_flag? 'w'
			@wait = true
		end

		## Negative flags
		if has_flag? 'A'
			@all = false
		end
		if has_flag? /[DE]/
			@detach = false
		end
		if has_flag? 'T'
			@new_term = false
		end
		if has_flag? 'W'
			@wait = false
		end
	end

	def newway() true end

	def no_mode?()
		@mode == 0
	end

	def no_flags?()
		@flagstring.empty?
	end

	def default_flags=(x)
		if @flagstring.empty?
			self.flags = x
		end
		x
	end

	## set the mode and return self.
	def with_mode(n)
		@mode = n
		self
	end

	## wrapper {{{

	## escape all files for direct use in the shell.
	## if the _multi_ attribute is true, this is a shortcut for
	##   rc.paths.map {|x| ~x}.join(' ')
	## otherwise:
	##   ~(rc.paths.first)
	def ~
		if @multi
			@paths.map {|x| ~x}.join(' ')
		else
			~@paths.first
		end
	end

	## escape one (the first) file for direct use in the shell.
	## this is a shortcut for:
	##   ~(rc.paths.first)
	def one
		~@paths.first
	end

	## shortcut for _files.size_
	def size() @files.size end

	## shortcut for _files.first.path_
	def first() @files.first end

	## shortcut for _files.first.name_
	def name() @files.first.name end

	## }}}
end

