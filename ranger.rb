#!/usr/bin/ruby -Ku
version = '0.2.1'

# Log details
# 0 = do not log
# 1 = log fatalities
# 2 = log errors
# 3 = log everything
LOG_LEVEL = 3
#LOG_LEVEL = 0

require 'pathname'

def fj( *args ) File.join( *args ) end

$: << MYDIR = File.dirname(Pathname.new(__FILE__).realpath)


#SCREENSAVER = fj MYDIR, 'code', 'screensaver', 'clock.rb'

PID = Process.pid

if ARGV.size > 0
	case ARGV.first
	when '-k'
		exec "killall -9 fm"
	end
	pwd = ARGV.first
	if pwd =~ /^file:\/\//
		pwd = $'
	end

	unless File.exists?(pwd)
		pwd = nil
	end

else
	pwd = nil
end

#require 'ftools'
require 'pp'
require 'ostruct'
class OpenStruct; def __table__() @table end end
require 'thread'

require 'interface/ncurses.rb'
for file in Dir["#{MYDIR}/code/**/*.rb"]
	file.slice! 0..MYDIR.size
	require file
end

unless ARGV.empty? or File.directory?(pwd)
	exec(Fm.getfilehandler_frompath(pwd))
end

include Interface
include Debug

ERROR_STREAM = File.open('/tmp/errorlog', 'a')

#def log(obj)
#	$stdout = ERROR_STREAM
#	pp caller
#	pp obj
#	$stdout.flush
#	$stdout = STDOUT
#	obj
#end

begin
	Fm.initialize( pwd )
	Fm.main_loop
ensure
	log "exiting!"
	log ""
	closei if Interface.running?
#	Fm.dump
	ERROR_STREAM.close

	# Kill all other threads
	for thr in Thread.list
		unless thr == Thread.current
			thr.kill
		end
	end
end

