require 'ncurses'
require 'code/debug'

module Color
	extend Color

	COLORSCHEMEDIR = File.join(MYDIR, 'data', 'colorscheme')
	def load_colorscheme(name)
		## colorschemes are located in data/colorscheme/
		fname = File.join(COLORSCHEMEDIR, "#{name}.rb")
		assert File.exists?(fname), "No such colorscheme: #{fname}"
		
		clear_all
		load fname
#		::Console.write("Colorscheme #{name} loaded.")
	end

	def clear_all()
		clear
		for key, type in TYPES
			type.clear
		end
	end

	def clear
		for var in instance_variables
			instance_variable_set(var, nil)
		end
	end

	def default() -1 end
	def black()    0 end
	def red()      1 end
	def green()    2 end
	def yellow()   3 end
	def blue()     4 end
	def magenta()  5 end
	def cyan()     6 end
	def white()    7 end

	alias df default
	alias brown yellow
	alias orange yellow
	alias purlpe magenta
	alias pink magenta
	alias teal cyan
	alias gray white
	alias grey white

	def none()       Ncurses::A_NORMAL     end
	def bold()       Ncurses::A_BOLD       end
	def reverse()    Ncurses::A_REVERSE    end
	def underline()  Ncurses::A_UNDERLINE  end

	def standout()   Ncurses::A_STANDOUT   end
	def blink()      Ncurses::A_BLINK      end
	def dim()        Ncurses::A_DIM        end
	def protect()    Ncurses::A_PROTECT    end
	def invisible()  Ncurses::A_INVIS      end
	def altcharset() Ncurses::A_ALTCHARSET end
	def chartext()   Ncurses::A_CHARTEXT   end

	alias reversed reverse
	alias revert reverse
	alias invis invisible

	def default_color() return default, default, none end
	alias dc default_color

	## a shortcut.
	##    use %w{txt type left_side}
	## is equivalent to:
	##    def txt() @txt || @type || @left_side || @base end
	def self.use(arr)
		arr << 'base' unless arr.last == 'base'
		body = arr.map{|x| "@#{x}"}.join(' || ')
		eval "def #{arr.first}() #{body} end"
	end

	use %w{base}
	use %w{file}

	use %w{link file}
	use %w{badlink link file}
	use %w{goodlink link file}
	use %w{directory file}
	use %w{forbidden directory file}

	use %w{top}
	use %w{hostname top}
	use %w{currentdir top}
	use %w{currentfile top}

	use %w{butt}
	use %w{permissions butt}
	use %w{allowed permissions butt}
	use %w{denied permissions butt}
	use %w{date butt}
	use %w{info butt}

	use %w{media file}
	use %w{video media file}
	use %w{sound media file}
	use %w{image media file}
	use %w{executable file}
	use %w{script executable file}
	use %w{binary executable file}

	module Type
		include Color

		ATTRIBUTES = %w[
			base file directory media executable
			video sound image
			script binary
			link goodlink badlink

			terminal_cursor error info
		]

		for a in ATTRIBUTES
			eval <<-DONE
				def #{a}()
					@#{a}_cache ||= @#{a} || super || Color.#{a} || default_color
				end
			DONE
		end

		## this is only meant to be used in Color
		def clear_all() nil end
	end

	module Normal;   extend Type end
	module Selected; extend Type end
	module Marked;   extend Type end
	module Console;  extend Type end

	module SelectedCurrentRow; extend Type end

	def [](x)      TYPES[x] end

	TYPES = {
		:normal   => Normal,
		:selected => Selected,
		:marked   => Marked,
		:console  => Console,
		:selected_current_row => SelectedCurrentRow
	}

	for key, val in TYPES
		eval "def #{key}() #{val} end"
	end
end

