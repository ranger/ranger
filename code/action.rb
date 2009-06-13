module Action
	extend self

	def close_interface
		closei
	end

	def start_interface
		starti
	end

	def copy(files, path)
		files = [files] unless files.is_a? Array
		unless files.empty?
			CopyBar2.new(files, path)
		end
	end

	def move(files, path)
		files = [files] unless files.is_a? Array
		unless files.empty?
			MoveBar2.new(files, path)
		end
	end

	def run(rc = nil)
		rc ||= RunContext.new(Fm.getfiles)
		assert rc, RunContext

		cf       = Fm.currentfile
		
		all      = rc.all.or true
		files    = rc.files.or(all ? Fm.selection : [cf])
		mode     = rc.mode.or 0
		newway   = rc.newway.or false

		return false if files.nil?

		if newway
#			logpp files.first.handler
#			rc = Fm.filehandler(files, struct)
			handler = rc.exec
		else
			handler, wait = Fm.getfilehandler(*files)
		end

		return false unless handler

		wait     = rc.wait.or wait
		new_term = rc.new_term.or false
		detach   = rc.detach.or false

		log handler
		if detach
			run_detached(handler, new_term)
		else
			run_inside(handler, wait)
		end
		return true
	end

	def run_detached(what, new_term)
		if new_term
			p = fork { exec('x-terminal-emulator', '-e', 'bash', '-c', what) }
#			Process.detach(p)
		else
			p = fork { exec "#{what} 2>> /dev/null >> /dev/null" }
			Process.detach(p)
		end
	end

	def run_inside(what, wait)
		close_interface
		system(*what)
		wait_for_enter if wait
		start_interface
	end

	def wait_for_enter
		print "Press [ENTER] to continue..."
		gets
	end
end

