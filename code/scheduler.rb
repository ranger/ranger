require 'thread'

# This thread inspects directories
module Scheduler
	extend self

	UPDATE_SIGNAL = 31
	PRIORITY = -1

	def reset()
		@scheduled = []
		@active = false

		@thread ||= Thread.new do
			## I have two ways of doing this. the first is somewhat better
			## but leads to problems with ncurses:
			## sometimes if you close the terminal window by clicking on
			## the X or pressing alt+F4 or in any other way that the window
			## manager provides, it will not properly exit and keep running
			## in the background, using up 100% CPU.
			if Option.evil
				Thread.current.priority = PRIORITY

				while true
					Thread.stop
					manage unless @scheduled.empty? or !@active
				end

			else
				while true
					sleep 0.1
					manage unless @scheduled.empty? or !@active
				end
			end
		end
	end

	def run
		@active = true
	end

	def stop
		@active = false
	end

	def <<(dir)
		dir.scheduled = true
		unless @scheduled.include? dir
			@scheduled << dir
		end
		@thread.run if Option.evil
	end

	private
	def manage
		while dir = @scheduled.shift
			dir.refresh(true)
			dir.resize
		end
		force_update
	end

	def force_update
		Process.kill( UPDATE_SIGNAL, Process.pid )
	end
end

