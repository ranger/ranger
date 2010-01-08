# Copyright (c) 2009, 2010 hut <hut@lavabit.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

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
			p = fork { exec "#{what} 2>> /dev/null >> /dev/null < /dev/null" }
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

	def delete!(*entries)
		for file in entries
			if file.is_a? Directory::Entry
				file = file.path
			end

			begin
				FileUtils.remove_entry_secure(file)
			rescue
				begin
					FileUtils.remove_entry(file)
				rescue
					lograise
				end
			end
		end
	end
end

