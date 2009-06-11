## just a little module for easier debugging of ncurses CLI applications
## where it's a bad idea to write debug info directly into the console.
## use this with: include Debug

require 'pp'

module Debug
	def self.setup(name, stream=nil, level=nil)
		if name.is_a? Hash
			stream  = name[:stream]
			level   = name[:level]
			name    = name[:name]
		end

		@@name   = name   || 'debug'
		@@stream = stream || STDOUT
		@@level  = level  || 3
		@@level  = 3

		@@stream.sync = true
	end

	def self.write(str)
		@@stream.write(str)
		return str
	end
	
	def self.puts(str)
		@@stream.puts(str)
		return str
	end

	def try(&block)
		return unless block
		begin
			yield
		rescue Exception
		end
	end

	## if you don't want your program to stop,
	## but still want to retrieve the error information
	def lograise(e=nil)
		e ||= $!
		log_err("#{e.class}: #{e.message}")
		log_err(e.backtrace)
	end

	def bm(descr="benchmark", &block)
		if @@level == 0
			yield
			return
		end

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

	def __logwrite__(obj, level)
		if level <= @@level
			Debug.write(obj)
		end
		obj
	end

	def __log__(obj, level)
		if level <= @@level
			obj = obj.nil? ? "checkpoint at #{Time.now}" : obj
			Debug.puts(obj)
		end
		obj
	end

	def __logpp__(obj, level)
		if level <= @@level
			old_stdout = $stdout
			$stdout    = @@stream

			pp(obj)

			$stdout    = old_stdout
		end
		obj
	end

	## each send a different level to __logXYZ__

	def logfatal(      obj = nil ) __log__(     obj, 1)  end
	def logppfatal(    obj = nil ) __logpp__(   obj, 1)  end
	def logwritefatal( obj = nil ) __logwrite__(obj, 1)  end

	def logerr(        obj = nil ) __log__(     obj, 2)  end
	def logpperr(      obj = nil ) __logpp__(   obj, 2)  end
	def logwriteerr(   obj = nil ) __logwrite__(obj, 2)  end

	def log(           obj = nil ) __log__(     obj, 3)  end
	def logpp(         obj = nil ) __logpp__(   obj, 3)  end
	def logwrite(      obj = nil ) __logwrite__(obj, 3)  end

	def trace(         n = 1     ) __log__(caller(n), 3) end

	alias log_fatal logfatal
	alias logpp_fatal logppfatal
	alias logwrite_fatal logwritefatal
	alias log_err logerr
	alias logpp_err logpperr
	alias logwrite_err logwriteerr
end

