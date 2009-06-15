module Application
	def aunpack(files)
		case files.mode
		when 0; "aunpack #{files}"
		when 1; "aunpack -l #{files} | less"
		end
	end

	def gedit(files)
		"gedit #{files}"
	end

	def totem(files)
		case files.mode
		when 0; "totem --fullscreen #{files}"
		when 1; "totem #{files}"
		end
	end

	def mplayer(files)
		case files.mode
		when 0; "mplayer -fs -sid 0 #{files}"
		when 1; "mplayer -sid 0 #{files}"
		when 2; "mplayer -vm sdl -sid 0 #{files}"
		else nil end
	end

	def mplayer_detached(files)
		files.base_flags = 'd'
		mplayer(files)
	end

	def evince(files)
		"evince #{files}"
	end

	def feh(files)
		case files.mode
		when 0; "feh #{files}"
		when 1; "feh --bg-scale #{files.one}"
		when 2; "feh --bg-tile #{files.one}"
		when 3; "feh --bg-center #{files.one}"
		when 4; "gimp #{files}"
		when 5; "feh -F #{files}"
		else nil end
	end

	def interpreted_language(files)
		case files.mode
		when 1; run(files)
		when 0; vi(files)
		else nil end
	end

	def zsnes(files)
		"zsnes #{files.first}"
	end

	def run(files)
		files.first.executable? ? "#{files.one}" : nil
	end

	def vi_or_run(files)
		case files.mode
		when 1; run(files)
		when 0; vi(files)
		else nil end
	end

	def vi(files)
		commands = [
			'map h :quit<cr>',
			'map q h',
			'map H :unmap h<CR>:unmap H<CR>:unmap q<CR>',
		].map {|x| "+'#{x}'"}.join(' ')

		"vi #{commands} #{files}"
	end

	def javac(files)
		check files
		"javac #{files}"
	end

	def java(files)
		"java #{files.files.map{|x| ~x.before_last('.')}.join(' ')}"
	end

	def firefox(files)
		"firefox #{files}"
	end

	def make(files)
		case files.mode
		when 0; "make"
		when 1; "make install"
		when 2; "make clear"
		else nil end
	end
	
	def rake(files)
		"rake"
	end
end

