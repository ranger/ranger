class Directory::Entry
	INTERPRETED_LANGUAGES = %w[haskell perl python ruby sh]
	MOVIE_EXTENSIONS = %w[avi mpg mpeg mp4 mp5 ogv ogm wmv mkv flv fid vob div divx]

	def get_handler
		## directories or sockets don't have any handler
		use.no_handler if dir? or socket?

		case @basename
		when 'Makefile'
			log "i use make"
			use.make
		when /^[Rr]akefile(.rb)?$/
			use.rake
		end

		## at first, look at the mime type
		case @mimetype
		when /^video|audio/
			use.mplayer

		when "application/pdf"
			use.evince

		when /^image/
			use.feh

		when /^(text|application)\/x-(#{INTERPRETED_LANGUAGES.join('|')})$/
			use.interpreted_language

		when 'text/x-java'
			use.javac

		when 'application/java-vm'
			use.java

		when 'text/html', 'application/x-shockwave-flash'
			use.firefox

		end

		## second, look at the extension
		case @ext
		when 'swc', 'smc'
			use.zsnes

		end

		## otherwise use vi
		use.vi
	end
end

