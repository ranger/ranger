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
			if EVIL
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
#		@active = true
	end

	def stop
		@active = false
	end

	def <<(dir)
		dir.scheduled = true
		unless @scheduled.include? dir
			@scheduled << dir
			if EVIL
				@thread.run
			end
		end
	end

	private
	def manage
		while dir = @scheduled.shift
			dir.refresh(true)
			dir.resize
			force_update
		end
	end

	def force_update
		Process.kill( UPDATE_SIGNAL, PID )
	end
end

