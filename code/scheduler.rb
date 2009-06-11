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
#			Thread.current.priority = PRIORITY
			while true
				sleep 0.1
				if @active and not @scheduled.empty?
					while dir = @scheduled.shift
						dir.refresh(true)
						dir.resize
						force_update
					end
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
		unless include? dir
			@scheduled << dir
		end
	end

	def include?(dir)
		@scheduled.include?(dir)
	end

	def force_update
		Process.kill( UPDATE_SIGNAL, PID )
	end

#	def priority() @thread.priority end
#	def priority=(x) @thread.priority=(x) end

end
