require 'pp'

module Debug
	@@logfile = '/tmp/errorlog'
	@@logstream = File.open(@@logfile, 'a')

	def self.write(str)
		@@logstream.write(str)
		@@logstream.flush
		return str
	end
	def self.puts(str)
		@@logstream.puts(str)
		@@logstream.flush
		return str
	end

	def try(&block)
		return unless block
		begin
			yield
		rescue Exception
		end
	end

	if LOG_LEVEL > 0
		def bm(descr="benchmark", &block)
			# Benchmark
			t1 = Time.now
			yield
			dur = Time.now-t1

			# substract the durtation of a "bm(..) do end"
			dur -= bm_dummy(descr) do end

			# Format the duration
			dur *= 1000
			dur = dur > 0 ? dur : 0
			dur = '%0.3f' % dur
			logerr("#{descr}: #{dur}ms")
		end

		def bm_dummy(descr="benchmark", &block)
			t1 = Time.now
			yield
			return (Time.now-t1)
		end

		def __log__(obj, level)
			if level <= LOG_LEVEL
				obj = obj.nil? ? "checkpoint at #{Time.now}" : obj
				Debug.puts(obj)
			end
		end
		def __logpp__(obj, level)
			if level <= LOG_LEVEL
				$stdout = @@logstream
				pp obj
				$stdout.flush
				$stdout = STDOUT
			end
		end

		def logfatal(obj = nil) __log__(obj, 1) end
		def logppfatal(obj = nil) __logpp__(obj, 1) end

		def logerr(obj = nil) __log__(obj, 2) end
		def logpperr(obj = nil) __logpp__(obj, 2) end

		def log(obj = nil) __log__(obj, 3) end
		def logpp(obj = nil) __logpp__(obj, 3) end

		def trace() __logpp__(caller, 3) end
	else
		def __log__(a, b) end
		def __logpp__(a, b) end

		def logfatal(a=nil) end
		def logppfatal(a=nil) end

		def logerr(a=nil) end
		def logpperr(a=nil) end

		def log(a=nil) end
		def logpp(a=nil) end
		def trace() end
		def bm(*args, &block) yield end
	end
end
