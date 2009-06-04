#!/usr/bin/ruby -Ku

# Log details
# 0 = do not log
# 1 = log fatalities
# 2 = log errors
# 3 = log everything
LOG_LEVEL = 3
#LOG_LEVEL = 0

require 'pathname'

def File::resolve_symlink( path = __FILE__ )
	Pathname.new(path).realpath
end

def require_from_here ( *list )
	require File.join( FM_DIR, *list )
end

def fj( *args ) File.join( *args ) end

$: << FM_DIR = File::dirname(File::resolve_symlink)

#SCREENSAVER = fj FM_DIR, 'code', 'screensaver', 'clock.rb'

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

require_from_here 'interface/ncurses.rb'
require_from_here 'code/extensions/basic.rb'
require_from_here 'code/extensions/fileutils.rb'
require_from_here 'code/fm.rb'
require_from_here 'code/keys.rb'
require_from_here 'code/types.rb'
require_from_here 'code/bars.rb'
require_from_here 'code/action.rb'
require_from_here 'code/draw.rb'
require_from_here 'code/directory.rb'
require_from_here 'code/debug.rb'

# Screensaver
require_from_here 'code/screensaver/clock.rb'

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
	Fm.dump
	ERROR_STREAM.close

	# Kill all other threads
	for thr in Thread.list
		unless thr == Thread.current
			thr.kill
		end
	end
end

