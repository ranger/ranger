module Fm
	MIMETYPES = Marshal.load(File.read(
		File.join(MYDIR, 'data', 'mime.dat')))

	def self.get_default_flags(file)
		case file.mimetype
		when /^(?:image|video)\//; 'd'
		when 'application/pdf'; 'd'
		else '' end
	end

	def self.filehandler(files, hash)
		str = files.map{|x| x.sh}.join(' ')
		type = files.first.mimetype
		name = files.first.basename
		mode = hash.mode

		use = lambda do |sym|
			hash.exec = App.send(sym, mode, name, str, files)
		end

		case type
		when /^(video|audio)\//
			use.call :mplayer
		when "application/pdf"
			use.call :evince
		when /^(image)\//
			use.call :image
		else
			case name
			when /\.(swc|smc)/
				use.call :zsnes
			end
		end

		return hash
	end

	module App
		def image(mode, name, str, file)
			case mode
			when 4; "feh --bg-scale #{str}"
			when 5; "feh --bg-tile #{str}"
			when 6; "feh --bg-center #{str}"
			when 2; "gimp #{str}"
			when 1; "feh -F #{str}"
			else "feh #{str}"
			end
		end
		def evince(mode, name, str, file)
			"evince #{str}"
		end
		def mplayer(mode, name, str, files)
			rest = name, str, files

			case mode
			when nil
				if name =~ /720p/
					mplayer(1, *rest)
				else
					mplayer(0, *rest)
				end
			when 0
				return "mplayer -fs -sid 0 #{str}"
			when 1
				return "mplayer -vm sdl -sid 0 #{str}"
			end
		end
		def zsnes(mode, name, str, files)
			case mode
			when 1
				return "zsnes -ad sdl -o #{str}"
			else
				return "zsnes -ad sdl -u -o #{str}"
			end
		end

		module_function(*%w{
			mplayer zsnes evince image
		})
	end

	def self.getfilehandler_frompath(*files)
		file = files.first
		n = files.size
		case file
		when /\.(part|avi|mpe?[g\d]|flv|fid|mkv|mov|wm[av]|vob|php|divx?|og[gmv])$/i
			if file =~ /720p/
				return "mplayer -vm sdl #{file.sh}", false
			else
				return "mplayer -fs #{file.sh}", false
			end

		when /\.java$/
			return "javac #{file.sh}", true

		when /\.class$/
			return log "java #{file.sh.before_last('.')}"

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

		when /\.(jpe?g|png|gif)$/i
			return "feh #{file.sh}", false

		when /\.(html?|swf)$/i
			return "firefox #{file.sh}"

		when /\.pdf$/i
			return "evince #{file.sh}"

		when /\.txt$/i
			return VI % file.sh

		when /\.wav$/i
			return "aplay -q #{file.sh}"

		when /\.m3u$/i
#			return "mpc play #{File.expand_path(file)[13..-1].sh}", false
			return "/home/hut/bin/loadplaylist.rb #{file.sh}"
#			return "cmus-remote -c && cmus-remote -P #{file} && cmus-remote -C 'set play_library=false' && sleep 0.3 && cmus-remote -n", false

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

