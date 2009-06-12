OPTIONS = {
	'hidden' => false,
	'sort' => :name,
	'dir_first' => true,
	'sort_reverse' => false,
	'color' => true,
	'filepreview' => true,
}

class Void
	oldv, $-v = $-v, nil

	for method in instance_methods
		remove_method(method) rescue nil
	end

	def self.method_missing(*a) end

	$-v = oldv
end

module Fm
	extend self
	COPY_PRIORITY = -2

	COLUMNS = 4
	VI = "vi -c 'map h :quit<CR>' -c 'map q :quit<CR>'" <<
		" -c 'map H :unmap h<CR>:unmap H<CR>' %s"
	
	def self.initialize(pwd=nil)
		@bars = []
		@bars_thread = nil
		
		@buffer = ''
		@pwd = nil
		@search_string = ''
		@copy = []
		@ignore_until = nil
		@trash = File.expand_path('~/.trash')
		pwd ||= Dir.getwd

		# `' and `` are the original PWD unless overwritten by .fmrc
		@memory = {
			'`' => pwd,
			'\'' => pwd
		}

		# Read the .fmrc
		@fmrc = File.expand_path('~/.fmrc')
		if (File.exists?(@fmrc))
			loaded = Marshal.load(File.read(@fmrc)) rescue nil
			if Hash === loaded
				@memory.update(loaded)
			end
		end

		# `0 is always the original PWD
		@memory['0'] = pwd

		# Give me some way to redraw screen while waiting for
		# input from CLI.geti

#		for i in 1..20
#			eval "Signal.trap(#{i}) do
#				log #{i}
#				exit if #{i} == 9 end"
#		end

		boot_up(pwd)
	end

	attr_reader(:dirs, :pwd)

	def pwd() @pwd end

	def refresh()
		begin
			@pwd.refresh
			draw
		rescue
		end
	end

	def boot_up(pwd=nil)
		pwd ||= @pwd.path || Dir.getwd
		Scheduler.reset

		@dirs = Hash.new() do |hash, key|
			hash[key] = newdir = Directory.new(key)
#			newdir.schedule
			newdir
		end

		@path = [@dirs['/']]
		enter_dir(pwd)

		Scheduler.run
	end

	def lines
		CLI::lines - @bars.size
	end

	def dump
		remember_dir
		dumped = Marshal.dump(@memory)
		File.open(@fmrc, 'w') do |f|
			f.write(dumped)
		end
	end

	def on_interrupt
		@buffer = ''
		sleep 0.2
	end

	def main_loop
		bool = false
		while true
			exit if Process.ppid == 1
			if @pwd.size == 0 or @pwd.pos < 0
				@pwd.pos = 0
			elsif @pwd.pos >= @pwd.size - 1
				@pwd.pos = @pwd.size - 1
			end

			begin
				draw()
			rescue Interrupt
				on_interrupt
#			rescue Exception
#				log($!)
#				log(caller)
			end

			begin
#				unless bool
#					bool = true
					key = geti
#				else
#					key = geti
#					key = 'j'
#				end
#				@mutex.synchronize {
					press(key)
#				}
			rescue Interrupt
				on_interrupt
			end
		end
	end

	def current_path() @pwd.path end

	def reset_title() set_title("fm: #{@pwd.path}") end

	def enter_dir_safely(dir)
		dir = File.expand_path(dir)
		if File.exists?(dir) and File.directory?(dir)
			olddir = @pwd.path
			begin
				enter_dir(dir)
				return true
			rescue
				log("NIGGER" * 100)
				log($!)
				log(caller)
				enter_dir(olddir)
				return false
			end
		end
	end

	def enter_dir(dir)
		@pwd.restore if @pwd
		@marked = []
		dir = File.expand_path(dir)

		oldpath = @path.dup

		# NOTE: @dirs[unknown] is not nil but Directory.new(unknown)
		@path = [@dirs['/']]
		unless dir == '/'
			dir.slice(0)
			accumulated = '/'
			for part in dir.split('/')
				unless part.empty?
					accumulated = File.join(accumulated, part)
					@path << @dirs[accumulated]
				end
			end
		end

		@pwd = @path.last
		@pwd.pos = @pwd.pos

		@pwd.files_raw.dup.each do |x|
			@dirs[x] if File.directory?(x)
		end

		reset_title()

		if @path.size < oldpath.size
			@pwd.pos = @pwd.files_raw.index(oldpath.last.path) || 0
		end

		i = 0

		@path.each_with_index do |p, i|
			p.schedule
			unless i == @path.size - 1
				p.pointed_file = @path[i+1].path
			end
		end

		Dir.chdir(@pwd.path)
	end

	def currentfile() @pwd.files[@pwd.pos] end
	def selection()
		if @marked.empty?
			[currentfile]
		else
			@marked.dup
		end
	end

	def move_to_trash!(fn)
		unless File.exists?(@trash)
			Dir.mkdir(@trash)
		end
		new_path = File.join(@trash, fn.basename)

		Action.move(fn, new_path)

		return new_path
	end

	def move_to_trash(file)
		unless file
			return
		end

		if String === file
			file = Directory::Entry.new(file)
		end

		if file.exists?
			if file.dir?
				if !file.in?(@trash) and file.size > 0
					return move_to_trash!(file)
				else
					Dir.rmdir(file.path) rescue nil
				end
			elsif file.symlink?
				file.delete!
			else
				if !file.in?(@trash) and file.size > 0
					return move_to_trash!(file)
				else
					file.delete!
				end
			end
		end
		return nil
	end

	def bar_add(bar)
		if @bars.empty?
			# This thread updates the statusbars
			@bars_thread = Thread.new do
				while true
					draw_bars
					sleep 0.5
				end
			end
		end
		@bars << bar
	end

	def bar_del(bar)
		@bars.delete(bar)
		if @bars.empty?
			@bars_thread.kill
			@bars_thread = nil
		end
	end
end

