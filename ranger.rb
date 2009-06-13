#!/usr/bin/ruby -Ku
version = '0.2.3'

require 'pathname'
$: << MYDIR = File.dirname(Pathname.new(__FILE__).realpath)

EVIL = false

if ARGV.size > 0
	case ARGV.first
	when '-k'
		exec "killall -9 #{File.basename($0)}"
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

for file in Dir.glob "#{MYDIR}/code/**/*.rb"
	require file [MYDIR.size + 1 ... -3]
end

load 'data/types.rb'
load 'data/apps.rb'
load 'data/colorscheme/default.rb'
load 'data/screensaver/clock.rb'

include Debug

Debug.setup( :name   => 'nyuron',
             :stream => File.open('/tmp/errorlog', 'a'),
             :level  => 3 )

ERROR_STREAM = File.open('/tmp/errorlog', 'a')

if pwd and !ARGV.empty? and !File.directory?(pwd)
	file = Directory::Entry.new(pwd)
	file.get_data
	Action.run(RunContext.new(file, 0, 'c'))
	exit
end

include CLI

Signal.trap(Scheduler::UPDATE_SIGNAL) do
	Fm.refresh
end

begin
	Fm.initialize( pwd )
	Fm.main_loop
ensure
	log "exiting!"
	log ""
	closei if CLI.running?
	Fm.dump
	ERROR_STREAM.close

	# Kill all other threads
	for thr in Thread.list
		unless thr == Thread.current
			thr.kill
		end
	end
end

