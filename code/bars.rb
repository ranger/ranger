#class Bar
#	def initialize( text = '' )
#		@text = text
#		@text_prefix = nil
#		@max = 0
#		@done = 0
#		@counter = 0
#		@thread = nil
#		@update_proc = nil
#		Fm.bar_add(self)
#	end
#
#	def kill(evil = true)
#		Fm.bar_del(self)
#		Fm.force_update
#
#		@thread.kill
#	end
#
#	def update(&block)
#		if block
#			@update_proc = block
#		elsif @update_proc
#			@update_proc.call(self)
#		end
#	end
#
#	def set_text_prefix(text)
#		@text_prefix = text
#	end
#	def set_text(text)
#		@text_prefix = nil
#		@text = text
#	end
#	alias text= set_text
#
#	attr_accessor :thread, :counter, :max
#end
#
#class CopyBar < Bar
#	def initialize( text = '' )
#		super
#
#		@update_proc = proc do |b|
#			begin
#				b.done = File.size(fname).to_f / finished
#			rescue
#				b.done = 0
#			end
#		end
#	end
#end

class Bar2
	def kill(evil = true)
		Fm.bar_del(self)
		Fm.force_update

		@thread.kill
	end

	def set_text_prefix(text)
		@text_prefix = text
	end
	def set_text(text)
		@text_prefix = nil
		@text = text
	end
	alias text= set_text

	attr_accessor :thread, :counter, :max
	def done
		if @counter.is_a? MutableNumber
			@counter.value.to_f / @max
		else
			0
		end
	end

	def update() end

	def text
		if @text_prefix
			"#{@text_prefix} #{(@counter.value.to_f * 10000/ @max).round.to_f/100}%"
		elsif @text
			@text
		else
			""
		end
	end
end

class CopyOrMoveBar < Bar2
	def initialize(files, path)
		path = path.path unless path.is_a? String
		Fm.bar_add(self)
		log([files, path])

		
		@thread = Thread.new do
			begin
				for file in files
					file = file.path unless file.is_a? String
					if File.exists?(file)
						run_operation(file, path)
					end
				end
			rescue
				log $!
				log $!.backtrace
			ensure
				kill(false)
			end
		end
		@thread.priority = Fm::COPY_PRIORITY
	end
end

class CopyBar2 < CopyOrMoveBar
	def run_operation(file, path)
		if File.directory?(file)
			FileUtils.cp_r_in_bar(self, file, path)
		else
			FileUtils.cp_in_bar(self, file, path)
		end
	end
end

class MoveBar2 < CopyOrMoveBar
	def run_operation(file, path)
		FileUtils.mv_in_bar(self, file, path)
	end
end

