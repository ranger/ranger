#!/usr/bin/ruby -Ku
version = '0.2.4'

require 'pathname'
$: << MYDIR = File.dirname(Pathname(__FILE__).realpath)

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

## default options
opt = {
	:show_hidden            => false,
	:sort                   => :name,
	:dir_first              => true,
	:sort_reverse           => false,
	:cd                     => ARGV.include?('--cd'),
	:colorscheme            => true,
	:bookmark_file          => '~/.ranger_bookmarks',
	:ascii_only             => true,
	:wide_bar               => true,
	:confirm_string         => "yes I am!",
	:confirm                => true,
	:file_preview           => true,
	:preview                => true,
	:colorscheme            => 'default'
}

class OptionClass < Struct.new(*opt.keys)
	def confirm_string; confirm ? super : "" end
end

Option = OptionClass.new(*opt.values)
opt = nil

load 'ranger.conf'
load 'data/colorscheme/' + Option.colorscheme + '.rb'
load 'data/screensaver/clock.rb'

include Debug

Debug.setup( :name   => 'nyuron',
             :file   => '/tmp/errorlog',
             :level  => 3 )

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

	Fm.dump_pwd_to_3 if Option.cd

	# Kill all other threads
	for thr in Thread.list
		unless thr == Thread.current
			thr.kill
		end
	end
end

