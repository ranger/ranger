module Fm
	def self.getfilehandler_frompath(file)
		case file
		when /\.(part|avi|mpe?[g\d]|flv|fid|mkv|mov|wm[av]|vob|php|divx?|og[gmv])$/i
			if file =~ /720p/
				return "mplayer -vm sdl #{file.sh}", false
			else
				return "mplayer -fs #{file.sh}", false
			end

		when /\.part$/
			test = getfilehandler_frompath($`)
			if test
				return test
			end

		when /\.(swc|smc)$/i
			return "zsnes -ad sdl -u -o #{file.sh}"

		when /\.(zip|rar|tar|gz|7z|jar|bz2)$/i
			return "aunpack #{file.sh}", false

		when "Makefile"
			return "make"

		when /\.(jpe?g|png)$/i
			return "feh #{file.sh}", false

		when /\.html?$/i
			return "firefox #{file.sh}"

		when /\.pdf$/i
			return "evince #{file.sh}"

		when /\.txt$/i
			return VI % file.sh

		when /\.wav$/i
			return "aplay -q #{file.sh}"

		when /\.m3u$/i
			return "cmus-remote -c && cmus-remote -P #{file} && cmus-remote -C 'set play_library=false' && sleep 0.3 && cmus-remote -n", false

		end

	end
	def self.getfilehandler(file)
		test = getfilehandler_frompath(file.basename)
		if test
			return test
		end

		if file.executable?
			return "#{file.sh}", true
		end

		return VI % file.sh
	end
end

