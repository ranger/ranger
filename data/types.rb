## This file specifies WHAT program is run,
## depending on the file.
##
## as soon as a "use.myprogram" is reached,
## this programm will be used an the function
## is finished.

class Directory::Entry
	def get_handler
		## directories or sockets don't have any handler
		use.no_handler if dir? or socket?


		## first look at the basename
		case @basename
		when 'Makefile'
			use.make

		when /^[Rr]akefile(.rb)?$/
			use.rake
		end

		## then at the extension
		case @ext
		when 'svg'
			use.firefox
		when 'm4v'
			use.mplayer
		end

		## then look at the mime-type
		case @mimetype
		when /^video/
			use.mplayer_detached

		when /^audio/
			use.mplayer

		when "application/pdf"
			use.evince

		when /^image/
			use.feh

		when /^(text|application)\/x-(#{INTR})$/
			use.interpreted_language

		when 'text/x-java'
			use.javac

		when 'application/java-vm'
			use.java

		when 'text/html', 'application/x-shockwave-flash'
			use.firefox
		end


		## then at the extension again
		case @ext
		when 'swc', 'smc'
			use.zsnes

		when 'rar', 'zip', 'tar', 'gz', '7z', 'jar', 'bz', 'bz2'
			use.aunpack
		end


		## is it executable?
		use.vi_or_run if executable?

		## if there is nothing found, use a default application,
		## for example a text- or hex-editor.
		use.vi
	end

	## interpreted languages
	INTR = %w[haskell perl python ruby sh].join('|')
end

