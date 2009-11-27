# A Class that contains data about directories
class Directory
	class LoadStatus
		# @n contains a three bit number: x3x2x1
		# x1:
		# 0 = not scheduled
		# 1 = scheduled
		# x3x2:
		# 00 = nothing loaded
		# 01 = got the list of files
		# 10 = <undefined>
		# 11 = got the list of files and entry objects
		def initialize(n = 0)
			@n = 0
		end

		def got_files?
			# is bit 2 nd 3 == 01
			return n & 2 == 2
		end

		def scheduled?
			# is the first bit 1?
			return n & 1 == 1
		end

		def got_objects?
			return n & 4 == 4
		end
		attr_accessor :n
	end

	def initialize(path)
		@path = path
		@status = LoadStatus.new(0)
		@files = []
		@sort_time = nil
		@mtime = nil
#		@width = 1000
		@read = false
		@free_space = nil
		@empty = true
		@scheduled = false
	end

	# {{{ Trivial
	def inspect
		return "<Directory: #{path}>"
	end
	alias to_s inspect

	def size
		return @files.size
	end

	def not_loaded?
		return @level == 0
	end
	def file_list_loaded?
		return @level >= 1
	end
	def ready?
		return @level >= 2
	end
	# }}}
end
