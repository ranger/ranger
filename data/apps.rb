## This file defines programs, and HOW those
## programs are run.
##
## Look at the definition of "totem" for a
## fully documented example.


module Application
	## def totem(files) starts the definition of totem
	def totem(files)
		## this is the `case' statement.
		## it looks up the mode and does different
		## things depending on the mode.
		case files.mode

		## if the mode is 0 (default)
		when 0
			## start totem in fullscreen
			"totem --fullscreen #{files}"

		## if the mode is 1
		when 1
			## start totem normally
			"totem #{files}"
		end

		## the mode is a number which you type in
		## between two r's. for example, press:
		## r1r
		## to run the file in mode 1.
		## there are shortcuts: the key l runs in mode 0,
		## and L in mode 1.

		## the variable `files' is of a type RunContext,
		## see ranger/code/runcontext.rb for details.
	end


	def aunpack(files)
		case files.mode
		when 0; "aunpack #{files}"
		when 1; "aunpack -l #{files} | less"
		end
	end

	def gedit(files)
		"gedit #{files}"
	end

	def mplayer(files)
		case files.mode
		when 0; "mplayer -fs -sid 0 #{files}"
		when 1; "mplayer -fs -sid 0 -vfm ffmpeg -lavdopts lowres=1:fast:skiploopfilter=all:threads=8 #{files}"
		when 2; "mplayer -vm sdl -sid 0 #{files}"
		when 3; "mplayer -mixer software #{files}"
		when 4; "mplayer -vo caca #{files}"
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
		files.dont_run_in_background

		commands = [
			'map h ZZ',
			'map q h',
			'map H :unmap h<CR>:unmap H<CR>:unmap q<CR>',
		].map {|x| "+'#{x}'"}.join(' ')

		"vi #{commands} #{files}"
	end

	def javac(files)
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

	## set the default editor for when pressing E
	alias editor vi

end

