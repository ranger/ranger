module Application
	def mplayer(rc)
		check rc

		rc.default_flags = 'd'

		if rc.no_mode?
			rc.mode = (rc.name =~ /720p/) ? 2 : 1
		end

		case rc.mode
		when 1; "mplayer -fs -sid 0 #{~rc}"
		when 2; "mplayer -sid 0 #{~rc}"
		when 3; "mplayer -vm sdl -sid 0 #{~rc}"
		else nil end
	end

	def evince(rc)
		check rc
		"evince #{~rc}"
	end

	def feh(rc)
		check rc
		case rc.mode
		when 4; "feh --bg-scale #{rc.one}"
		when 5; "feh --bg-tile #{rc.one}"
		when 6; "feh --bg-center #{rc.one}"
		when 2; "gimp #{~rc}"
		when 1; "feh -F #{~rc}"
		else "feh #{~rc}"
		end
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
end

