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

