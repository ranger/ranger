require 'pp'

## This module helps to debug by:
## 1. defining log functions which write data into any kind of stream
## rather than to STDOUT, and are seperated into fatal, error and normal
## messages.
## 2. by defining assertion functions which raise an AssertionError
## if the assertion is false.
## 3. a couple of other nice things such as trace or bm (benchmark)
## 
## use this with:
##   include Debug
##   Debug.setup(...)
module Debug
	class AssertionError < StandardError; end

	## setup the debugger. optionally takes a hash like:
	##   Debug.setup(:name => 'foo', :level => 2)
	## parameters are:
	##   _name_: an identifier which is written before anything
	##   _stream_: a writable stream like STDERR or File.open('foo', 'a')
	##   _level_: the verbosity level.
	##     0: log nothing
	##     1: log fatal errors
	##     2: log all errors
	##     3: log everything
	def self.setup(name=nil, stream=nil, level=nil)
		if name.is_a? Hash
			stream  = name[:stream]
			level   = name[:level]
			name    = name[:name]
		end

		@@name   = name   || 'debug'
		@@stream = stream || STDERR
		@@level  = level  || 3
		@@level  = 3

		@@stream.sync = true
	end

	## Write something to the output stream.
	def self.write(str)
		@@stream.write(str)
		return str
	end
	
	## Write something to the output stream with a newline at the end.
	def self.puts(str)
		@@stream.puts(str)
		return str
	end

	## Passes if value is neither nil nor false.
	## The second argument is an optional message.
	## All other assert methods are based on this.
	def assert_true(value, message = nil)
		message ||= "#{value.inspect} is not true!"
		Kernel.raise(AssertionError, message, caller(0)) unless value
	end

	## Takes a good guess about what you want to do.
	## There are two options:
	##   1 or 2 arguments, of which the second must be a String
	##   => use assert_true(value, rest.first)
	##
	##   otherwise
	##   => use assert_match(value, *rest)
	def assert(value, *rest)
		if rest.size == 0 or rest.size == 1 and rest.first.is_a? String
			assert_true(value, rest.first)
		else
			assert_match(value, *rest)
		end
	end

	## Passes if "testX === value" is true for any argument.
	## If the last argument is a string, it will be used as the message.
	def assert_match(value, test0, *test)
		## test0 and *test are only seperated to force >=2 args
		## so put them back together here.
		test.unshift( test0 )

		## get or generate the message
		if test.last.is_a? String
			message = test.pop
		else
			message = "Expected #{value.inspect} to match with "
			message << if test.size == 1
				"#{test0.inspect}!"
			else
				"either #{test.map{|x| x.inspect}.join(" or ")}!"
			end
		end

		assert_true test.any? { |testX| testX === value }, message
	end

	## Passes if "value1 == value2"
	def assert_equal(value1, value2, message=nil)
		message ||= "#{value1.inspect} expected, got: #{value2.inspect}!"
		assert_true value1 == value2, message
	end

	## Passes if "value1 != value2"
	def assert_not_equal(arg1, arg2, message=nil)
		message ||= "Expected something other than #{arg1.inspect}!"
		assert_true arg1 != arg2, message
	end

	## Put this at positions which require attention.
	def forbid(message = nil)
		message ||= "Incomplete Code!"
		assert_true false, message
	end

	alias flunk forbid
	alias assert_neq assert_not_equal

	## Trace back the whole way from this function,
	## ommitting the first _n_ function calls
	def trace( n = 1 ) __log__( caller( n ), 3 ) end

	## if you don't want your program to stop,
	## but still want to retrieve the error information
	def lograise(e=nil)
		e ||= $!
		log_err("#{e.class}: #{e.message}")
		log_err(e.backtrace)
	end

	## Perform a benchmark on the given block. Optionally
	## takes a description which will be logged too.
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
		dur -= Debug.bm_dummy(descr) do end

		# Format the duration
		dur *= 1000
		dur = dur > 0 ? dur : 0
		dur = '%0.3f' % dur
		logerr("#{descr}: #{dur}ms")
	end

	## for better benchmark results
	def self.bm_dummy(descr="benchmark", &block)
		t1 = Time.now
		yield
		return (Time.now-t1)
	end

	## Log _obj_ by using "IO#write" if _level_ is smaller or equal
	## to the current verbose level. There will be some shortcuts:
	##   logwrite(x)      => __logwrite__(x, 3)
	##   logwriteerr(x)   => __logwrite__(x, 2)
	##   logwritefatal(x) => __logwrite__(x, 1)
	def self.__logwrite__(obj, level)
		if level <= @@level
			Debug.write(obj)
		end
		obj
	end

	## Log obj by using "IO#puts" if level is smaller or equal
	## to the current verbose level. There will be some shortcuts:
	##   log(x)      => __log__(x, 3)
	##   logerr(x)   => __log__(x, 2)
	##   logfatal(x) => __log__(x, 1)
	def self.__log__(obj, level)
		if level <= @@level
			obj = obj.nil? ? "checkpoint at #{Time.now}" : obj
			Debug.puts(obj)
		end
		obj
	end

	## Log obj by using "pp" (pretty-print) if level is smaller or equal
	## to the current verbose level. There will be some shortcuts:
	##   logpp(x)      => __logpp__(x, 3)
	##   logpperr(x)   => __logpp__(x, 2)
	##   logppfatal(x) => __logpp__(x, 1)
	def self.__logpp__(obj, level)
		if level <= @@level
			old_stdout = $stdout
			$stdout    = @@stream

			pp(obj)

			$stdout    = old_stdout
		end
		obj
	end

	## generate lots of shortcut functions for __log(pp|write)__
	for method in ['', 'pp', 'write']
		for key, level in { '' => 3, 'err' => 2, 'fatal' => 1 }
			eval <<-DONE
				def log#{method}#{key}( obj = nil )
					Debug.__log#{method}__( obj, #{level} )
				end
				unless key.empty?
					alias log#{method}_#{key} log#{method}#{key}
				end
			DONE
		end
	end
end

