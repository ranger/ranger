module Fm
	def self.getfilehandler(file)
		bn = File.basename(file)
		case bn
		when /\.(avi|mpe?g|flv|mkv|ogm|mov|mp4|wmv|vob|php|divx?|mp3|ogg)$/i
			return "mplayer -fs #{file.sh}", false
		when /\.(jpe?g|png)$/i
			return "feh #{file.sh}", false
		when /\.(pdf)$/i
			return "evince #{file.sh}"
		when /\.(txt)$/i
			return VI % file.sh
		when /\.wav$/i
			return "aplay -q #{file.sh}"
		when /\.m3u$/i
			return "cmus-remote -c && cmus-remote -P #{file} && cmus-remote -C 'set play_library=false' && sleep 0.3 && cmus-remote -n", false
		end

		if File.executable?(file)
			return "#{file.sh}", true
		end

		return VI % file.sh
	end
end

