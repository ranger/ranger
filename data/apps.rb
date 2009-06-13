module Application
	def mplayer(rc)
		check rc

		rc.base_flags = 'd'

#		if rc.no_mode?
#			rc.mode = (rc.name =~ /720p/) ? 2 : 1
#		end

		case rc.mode
		when 0; "mplayer -fs -sid 0 #{~rc}"
		when 1; "mplayer -sid 0 #{~rc}"
		when 2; "mplayer -vm sdl -sid 0 #{~rc}"
		else nil end
	end

	def evince(rc)
		check rc
		"evince #{~rc}"
	end

	def feh(rc)
		check rc
		case rc.mode
		when 0; "feh #{~rc}"
		when 1; "feh --bg-scale #{rc.one}"
		when 2; "feh --bg-tile #{rc.one}"
		when 3; "feh --bg-center #{rc.one}"
		when 4; "gimp #{~rc}"
		when 5; "feh -F #{~rc}"
		else nil end
	end

	def interpreted_language(rc)
		check rc
		case rc.mode
		when 1; rc.first.executable? ? "#{rc.one}" : nil
		when 0; vi(rc)
		else nil end
	end

	def zsnes(rc)
		check rc
		"zsnes #{~rc.first}"
	end

	def vi(rc)
		commands = [
			'map h :quit<cr>',
			'map q h',
			'map H :unmap h<CR>:unmap H<CR>:unmap q<CR>',
		].map {|x| "+'#{x}'"}.join(' ')

		"vi #{commands} #{~rc}"
	end

	def javac(rc)
		"javac #{~rc}"
	end

	def java(rc)
		"java #{rc.files.map{|x| ~x.before_last('.')}.join(' ')}"
	end

	def firefox(rc)
		"firefox #{~rc}"
	end

	def make(rc)
		case rc.mode
		when 0; "make"
		when 1; "make install"
		when 2; "make clear"
		else nil end
	end
	
	def rake(rc)
		"rake"
	end
end

