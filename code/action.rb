require 'fileutils'

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
			CopyBar.new(files, path)
		end
	end

	def move(files, path)
		files = [files] unless files.is_a? Array
		unless files.empty?
			MoveBar.new(files, path)
		end
	end

	def run(rc = nil)
		rc ||= RunContext.new(Fm.getfiles)
		assert rc, RunContext

		all      = rc.all.or false
		files    = rc.files
		mode     = rc.mode.or 0

		return false if files.nil? or files.empty?

		handler = rc.exec

		return false unless handler

		wait     = rc.wait.or wait
		new_term = rc.new_term.or false
		detach   = rc.detach.or false

		log handler
		if detach
			run_detached(handler, rc)
		else
			run_inside(handler, rc)
		end
		return true
	end

	def run_detached(what, rc)
		if rc.new_term
			p = fork { exec('x-terminal-emulator', '-e', 'bash', '-c', what) }
#			Process.detach(p)
		else
			p = fork { exec "#{what} 2>> /dev/null >> /dev/null" }
			Process.detach(p)
		end
	end

	def run_inside(what, rc)
		close_interface unless rc.console
		system(*what)
		wait_for_enter if rc.wait
		start_interface unless rc.console
	end

	def wait_for_enter
		print "Press [ENTER] to continue..."
		$stdin.gets
	end
end

