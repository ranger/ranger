require 'socket'

module Fm
	DONT_PREVIEW_THESE_FILES = /\.(avi|[mj]pe?g|iso|mp\d|og[gmv]|wm[av]|mkv|torrent|so|class|flv|png|bmp|vob|divx?)$/i

	def column_put_file(n, file)
		i = 0
		if OPTIONS['filepreview'] and file.path !~ DONT_PREVIEW_THESE_FILES
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

			fn = f.basename
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

			attr_at(l, left, fn.size.limit(wid-1), mycolor.send(clrname))
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
			return q, q

		when 2
			q = cols / 4
			w = @path.last.width.limit(cols/2, cols/8)
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
		elsif @buffer == '?'
			cleari
			puti 0, "      - - - Help - - -"
			puti 2, "   h/j/k/l: Movement    J/K: fast Movement"
			puti 3, "   H: Descend directory with respect to symlinks"
			puti 4, "   L: Wait for <Enter> after execution of a program"
			puti 6, "   t: Toggle Option     S: Change Sorting"
			puti 7, "   E: Edit file         s: Enter Shell"
			puti 8, "   rmdir: Remove whole dir  dD: Delete file or empty dir"
			puti 9, "   dd: Move file to ~/.trash and memorize it's new path"
			puti 10,"   yy: Memorize path    p: Copy memorized file here"
			puti 11,"   mv<place>: move file to place  mkdir<name>: obvious"
			puti 12,"   mX: Bookmark dir     'X: Enter bookmarked dir"
			puti 13,"   '': Enter last visited dir (note: ' and ` are equal)"
			puti 13,"   !<command> executes command"
			puti 15,"   To interrupt current operations: <Ctrl-C>"
			puti 16,"   To quit: q / ZZ / <Ctrl-D> / <Ctrl-C><Ctrl-C> (twice in a row)"
			puti 18,"   Press one of those keys for more information: g f"
		elsif @buffer == '?f'
			cleari
			puti 0, "      - - - Help - - -"
			puti 2, "   f<regexp> or /<regexp> searches for pattern and presses l"
			puti 3, "       when a matching file is found."
			puti 4, "       Pressing L in this mode is like pressing l outside"
			puti 6, "   F<regexp> like f but stay in this mode until <esc> is pressed"
		elsif @buffer == '?g'
			cleari
			puti 0, "      - - - Help - - -"
			puti 2, "   gg: go to top"
			puti 3, "   G:  go to bottom"
			puti 4, "   g0: go to /"
			puti 5, "   gu: go to /usr/"
			puti 6, "   gm: go to /media/"
			puti 7, "   ge: go to /etc/"
			puti 8, "   gh: go to ~/"
			puti 9, "   gt: go to ~/.trash/"
		else
			@pwd.recheck_stuff()
			cf = currentfile

			if cf and s0 = cf.mimetype
				puti 0, cols-s0.size, s0
			end

			s1 = ""
			s1 << Socket.gethostname
			s1 << ":"
			s2 = "#{@path.last.path}#{"/" unless @path.size == 1}"
			s3 = "#{cf ? cf.basename : ''}"
			
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
				if cf.dir?
					put_directory(3, @dirs[cf.path])
				elsif cf.file?
					column_put_file(3, cf)
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
			when 'S'
				puti btm, "Sort by (n)ame (s)ize (m)time (c)time (CAPITAL:reversed)"
			when 't'
				puti btm, "Toggle (h)idden_files (d)irs_first (c)olor (f)ilepreview"
			else
#				log(@pwd)
#				log "Buffer: #{@buffer}"
				attr_set(Color.base)
				attr_set(Color.info)
				puti btm, "#@buffer    #{@pwd.file_size.bytes(false)}, #{@pwd.free_space.bytes(false)} free, #{@pwd.size}, #{@pwd.pos+1}    ".rjust(cols)
				more = ''
				if cf.symlink?
					more = "#{cf.readlink}"
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
		@bars.each_with_index do |bar, ix|
			bar.update

			l = -ix - 1
			puti l, bar.text[0..cols-1].ljust(cols)
			done = bar.done
			c = (done * cols).to_i
			unless done == 0
#				color_at l, 0, c, 0, 4
			end
			unless done == cols
#				color_at l, c, -1, 0, 6
			end
		end
	end
end
