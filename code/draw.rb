require 'socket'

module Fm
	DONT_PREVIEW_THESE_FILES = /\.(avi|[mj]pe?g|iso|mp\d|og[gmv]|wm[av]|mkv|torrent|so|class|flv|png|bmp|vob|divx?)$/i

	def column_put_file(n, file)
		i = 0
		if Option.preview and Option.file_preview and file.path !~ DONT_PREVIEW_THESE_FILES
			m = lines - 2
			attr_set(Color.base)
			left, wid = get_boundaries(n)
			if false and file.ext =~ /(?:rar|zip|7z|tar|gz)$/ and file.size < 10485760
				text = `aunpack -l #{file.sh} 2>> /dev/null`
				text.each_line do |l|
					puti i+1, left, l[0, wid-1].ljust(wid)
					i += 1
					break if i == m
				end
			else
				File.open(file.path, 'r') do |f|
					check = true
					left, wid = get_boundaries(n)
					f.lines.each do |l|
						if check
							check = false
							break unless l.each_char.all? {|x| x[0] > 0 and x[0] < 128}
						end
						puti i+1, left, l.gsub("\t","   ")[0, wid-1].ljust(wid)
						i += 1
						break if i == m
					end
				end
			end
		end
		column_clear(n, i)
	end

	def put_directory(c, d)
		l = 1
		return column_clear(c, 0) unless d

		infos = (c == COLUMNS - 2)
		left, wid = get_boundaries(c)
		right = left + wid
		
		if not d.read?
			if (c == COLUMNS - 1) and @entering_directory
#				puti l, left, "reading...".ljust(wid+1)
				puti l, left, " " * (wid+1)
				column_clear(c, 1)
				@entering_directory = false
			end
			Scheduler << d
			return
		elsif d.read? and d.empty?
			puti l, left, 'empty'.ljust(wid+1)
			column_clear(c, 1)
			return
		end


		offset = get_offset(d, lines)
		(lines - 1).times do |l|
			lpo = l + offset
			l += 1

			break if (f = d.files[lpo]) == nil

			mycolor = if lpo == d.pos
				if infos
					Color.selected_current_row
				else
					Color.selected
				end
			elsif f.marked?
				Color.marked
			else
				Color.normal
			end

			dir = false

			clrname = if f.symlink?
				dir = f.dir?
				if f.broken_symlink?
					:badlink
				else
					:goodlink
				end
			elsif f.dir?
				dir = true
				:directory
			elsif f.movie?
				:video
			elsif f.audio?
				:sound
			elsif f.image?
				:image
			elsif f.executable?
				:executable
			else
				:file
			end

			fn = f.displayname
			fn = "* #{fn}" if f.marked?


			if infos
				myinfo = " #{f.infostring}  "
				sz = myinfo.size
				str = fn[0, wid-1].ljust(wid+1)
				if str.size > sz
					str[-sz..-1] = myinfo
					yes = true
				else
					yes = false
				end
				puti l, left, str
				attr_at(l, right-sz, sz, Color.normal.send(clrname))
			else
				puti l, left, fn[0, wid-1].ljust(wid+1)
			end

			if infos and Option.wide_bar
				attr_at(l, left-1, wid+1, mycolor.send(clrname))
			else
				attr_at(l, left, fn.size.limit(wid-1), mycolor.send(clrname))
			end
		end

		column_clear(c, l-1)
	end

	def self.column_clear(n, from=0)
		attr_set(Color.base)
		left, wid = get_boundaries(n)
		(from -1).upto(lines) do |l|
			puti l+2, left, ' ' * (wid+1)
		end
	end

	def self.get_offset(dir, max)
		pos = dir.pos
		len = dir.files.size
		max -= 2
		if len <= max or pos < max/2
			return 0
		elsif pos >= (len - max/2)
			return len - max
		else
			return pos - max/2
		end
	end

	def self.get_boundaries(column)
		cols = CLI.cols # to cache
		case column
		when 0
			return 0, cols / 8
			
		when 1
			q = cols / 8
			if !Option.preview# or (!Option.filepreview and !currentfile.dir?)
				return q, 2*q
#			elsif currentfile.path != DONT_PREVIEW_THESE_FILES
#				return q, 2*q
			else
				return q, q
			end

		when 2
			if !Option.preview
				q = cols * 0.375 - 1
				w = @path.last.width.limit(cols * 0.625, cols/8)
#			elsif currentfile.path =~ DONT_PREVIEW_THESE_FILES or (!Option.filepreview and !currentfile.dir?)
#				q = cols / 4
#				w = @path.last.width.limit(cols * 0.75, cols/8)
			else
				q = cols / 4
				w = @path.last.width.limit(cols/2, cols/8)
			end
			return q, w
			
		when 3
			l = cols / 4 + 1
			l += @path.last.width.limit(cols/2, cols/8)

			return l, cols - l
		end
	end

	def self.draw
		attr_set(Color.base)

		@cur_y = get_boundaries(COLUMNS-2)[0]

		if @buffer =~ /^block/
			screensaver
		elsif @buffer =~ /^\?/
			cleari
			puti 0, "   - - - Help - - -"
			if text = HELP[@buffer[1..-1]]
				i = 2
				text.each_line do |l|
					break if i == lines
					puti(i, l)
					i += 1
				end
			end
		elsif @buffer =~ /^o|`|'$/
			cleari
			i = 0
			case @buffer
			when 'o'; puti 0, "   move files to:"
			when '`', "'"; puti 0, "   go to:"
			end
			for key,val in @memory
				next if key == "'"
				break if key == lines
				puti i+=1, 2, "#{key} => #{val}"
			end
		else
			@pwd.recheck_stuff()
			cf = currentfile

			if cf and s0 = cf.mimetype
				puti 0, cols-s0.size, s0
			end

			s1 = "#{Socket.gethostname}:"
			s2 = "#{@path.last.path.ascii_only_if(Option.ascii_only)}#{"/" unless @path.size == 1}"
			s3 = "#{cf ? cf.displayname : ''}"

			if s0
				puti 0, (s1 + s2 + s3).ljust(cols-s0.size)
			else
				puti 0, (s1 + s2 + s3).ljust(cols)
			end

			bg = -1
			attr_at(0, 0, s1.size, *Color.hostname)
			attr_at(0, s1.size, s2.size, *Color.currentdir)
			attr_at(0, s1.size + s2.size, s3.size, *Color.currentfile)
#			color_at 0, 0, -1, 7, bg
#			color_at 0, 0, s1.size, 7, bg
#			color_at 0, s1.size, s2.size, 6, bg
#			color_at 0, s1.size + s2.size, s3.size, 5, bg

#			bold false

			begin
				if Option.preview
					if cf.dir?
						put_directory(3, @dirs[cf.path])
					elsif cf.file?
						column_put_file(3, cf)
					else
						column_clear(3)
					end
				else
					column_clear(3)
				end
			rescue
				column_clear(3)
			end

			pos_constant = @path.size - COLUMNS + 1

			(COLUMNS - 1).times do |c|
				pos = pos_constant + c

				if pos >= 0
					put_directory(c, @path[pos])
				else
					column_clear(c)
				end
			end

			attr_set(Color.base)
			btm = lines - 1

			case @buffer
			when /^delete/, /^dd/
				puti btm, "#@buffer    ".rjust(cols)
				puti btm, 'Are you serious? (' + Option.confirm_string + ')'

			when 'S'
				puti btm, "Sort by (n)ame (s)ize (m)time (c)time (e)xtension mime(t)ype (CAPITAL:reversed)"
			when 't'
				puti btm, "Toggle (h)idden_files (d)irs_first (f)ilepreview (p)review (w)idebar (c)d (!)confirm"
			else
				attr_set(Color.base)
				attr_set(Color.info)
				puti btm, "#@buffer    #{@pwd.file_size.bytes(false)}, #{@pwd.free_space.bytes(false)} free, #{@pwd.size}, #{@pwd.pos+1}    ".rjust(cols)
				more = ''
				if cf.symlink?
					more = "#{cf.readlink.ascii_only_if(Option.ascii_only)}"
				end

				attr_set(Color.date)
				left = "  #{Time.now.strftime("%H:%M:%S %a %b %d")}  "
				puti btm, left

				attr_set(cf.writable? ? Color.allowed : Color.denied)
				second = "#{cf.rights} "
				puti btm, left.size, second
				if more
					attr_set(cf.exists? ? Color.allowed : Color.denied)
					puti btm, left.size + second.size, "#{more} "
				end
			end

			attr_set(Color.base)
			draw_bars unless @bars.empty?

			movi(@pwd.pos + 1 - get_offset(@pwd, lines), @cur_y)
		end
		CLI.refresh
	end

	def self.draw_bars()
		l = CLI.lines
		@bars.each do |bar|
			bar.update

			l -= 1
			puti l, bar.text[0..cols-1].ljust(cols)
			done = bar.done
			c = (done * cols).to_i
			unless done == 0
				attr_at(l, 0, c, *Color.bar_done)
			end
			unless done == cols
				attr_at(l, c, -1, *Color.bar_undone)
			end
		end
	end
end
