# Generic extensions of the language

class MutableNumber
	attr_accessor :value

	def initialize(n=0)
		@value = n
	end
	def add(n=1) @value += n end
	def sub(n=1) @value -= n end
	def set(n)   @value  = n end
end

class Array
	def wrap(n)
		# TODO: this can be done better...
		if n >= 0
			n.times { push shift }
		else
			n.abs.times { unshift pop }
		end
	end
	def cdr(n = 1)
		self[n .. -1]
	end
	alias car first
	def sh
		map do |x|
			if x.respond_to? :path
				x.path.to_s
			else
				x.to_s
			end.sh
		end.join(" ")
	end
end

class String
	def clear
		self.replace("")
	end

	if RUBY_VERSION < '1.9'
		def ord
			self[0]
		end
	end

	def ascii_only()
		gsub(/[^!-~\s]/, '*')
	end

	def ascii_only_if(bool)
		bool ? ascii_only : dup
	end

	def from_first(str)
		self.include?(str) ? self [ self.index(str) + str.size .. -1 ] : nil
	end

	def from_last(str)
		self.include?(str) ? self [ self.rindex(str) + str.size .. -1 ] : nil
	end

	def split_at_last_dot()
		if ix = self.rindex('.')
			return self[0...ix], self[ix+1..-1]
		else
			return self, ''
		end
	end

	def before_last(str)
		self.include?(str) ? self [ 0 .. rindex(str) - str.size ] : self
	end

	def filetype()
		Directory::Entry::MIMETYPES[self] || 'unknown'
	end

	## encodes a string for the shell.
	##   peter's song.mp3 -> 'peter'\''s song.mp3'
	##
	##   system("mplayer #{ ~some_video_file }")
	def bash_escape
		"'#{bash_escape_no_quotes}'"
	end
	def bash_escape_no_quotes
		"#{ gsub("'", "'\\\\''") }"
	end
	alias ~ bash_escape
	alias sh bash_escape
end

class Numeric
	def limit(max, min = 0)
		self < min ? min : (self > max ? max : self)
	end

	def bytes(space = true, n_round = 2)
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

class File::Stat
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
	def modestr
		if symlink?
			result = 'l'
		elsif directory?
			result = 'd'
		else
			result = '-'
		end

		s = ("%o" % mode)[-3..-1]
		for m in s.each_byte do
			result << MODES_HASH[m.chr]
		end

		result
	end
end


class Object;   def or(value) self  end end
class NilClass; def or(value) value end end

