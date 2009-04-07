class Directory
	def initialize(path)
		@path = path
		@pos = 0
		@pointed_file = ''
		@width = 0
		refresh
	end

	attr_reader(:path, :files, :pos, :width, :infos)

	def pos=(x)
		@pos = x
		@pointed_file = @files[x]
		resize
	end

	def pointed_file=(x)
		if @files.include?(x)
			@pointed_file = x
			@pos = @files.index(x)
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
#				log File.basename(fn) + @infos[ix]
				sz = File.basename(fn).size + @infos[ix].size + 2
				@width = sz if @width < sz
			end
#			@width = @files[pos,lines-2].map{|x| File.basename(x).size}.max
		end
	end

	def get_file_infos()
		@infos = []
		@files.each do |fn|
			if File.directory?(fn)
				begin
					sz = Dir.entries(fn).size - 2
				rescue
					sz = "?"
				end
				@infos << "#{sz}"
			else
				if File.size?(fn)
					@infos << " #{File.size(fn).bytes 2}"
				else
					@infos << ""
				end
			end
		end
	end

	def refresh()
		glob = Dir.new(@path).to_a.sort!
		if OPTIONS['hidden']
		glob -= ['.', '..', 'lost+found']
		else
			glob.reject!{|x| x[0] == ?. or x == 'lost+found'}
		end
		if glob.empty?
			glob = ['.']
		end
		glob.map!{|x| File.join(@path, x)}
		dirs = glob.select{|x| File.directory?(x)}
		@files = dirs + (glob - dirs)

		get_file_infos
		resize

		if @pos >= @files.size
			@pos = @files.size - 1
		elsif @files.include?(@pointed_file)
			@pos = @files.index(@pointed_file)
		end
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

class Numeric
	def limit(max, min = 0)
		self < min ? min : (self > max ? max : self)
	end

	def bytes n_round = 2
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

		return flt.to_s + ' ' + a[i]
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
	def sh
		res = dup
		res.gsub!('\\\\', "\000")
		res.gsub!(' ', '\\ ')
		res.gsub!('(', '\\(')
		res.gsub!(')', '\\)')
		res.gsub!('*', '\\*')
		res.gsub!('\'', '\\\'')
		res.gsub!('"', '\\"')
		res.gsub!("\000", '\\\\')
		return res
	end
end

