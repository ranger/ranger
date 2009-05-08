module Action
	def self.copy(files, path)
		files = [files] unless files.is_a? Array
		unless files.empty?
			CopyBar2.new(files, path)
		end
	end

	def self.move(files, path)
		files = [files] unless files.is_a? Array
		unless files.empty?
			MoveBar2.new(files, path)
		end
	end

	def self.run(hash = {})
		unless OpenStruct === hash
			hash = OpenStruct.new(hash)
		end

		cf       = Fm.currentfile
		
		all      = hash.all.or true
		files    = hash.files.or(all ? Fm.selection : [cf])
		mode     = hash.mode.or 0
		newway   = hash.newway.or false

		return false if files.nil?

		if newway
			hash = Fm.filehandler(files, hash)
			handler = hash.exec
		else
			handler, wait = Fm.getfilehandler(*files)
		end

		return false unless handler

		wait     = hash.wait.or wait
		new_term = hash.new_term.or false
		detach   = hash.detach.or false

		log handler
		if detach
			run_detached(handler, new_term)
		else
			run_inside(handler, wait)
		end
		return true
	end

	def self.run_detached(what, new_term)
		if new_term
			p = fork { exec('x-terminal-emulator', '-e', 'bash', '-c', what) }
#			Process.detach(p)
		else
			p = fork { exec "#{what} 2>> /dev/null >> /dev/null" }
			Process.detach(p)
		end
	end

	def self.run_inside(what, wait)
		closei
		system(*what)
		gets if wait
		starti
	end
end

