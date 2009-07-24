module FileUtils
  def cp_in_bar(bar, src, dest, options = {})
    fu_check_options options, OPT_TABLE['cp']
    fu_output_message "cp#{options[:preserve] ? ' -p' : ''} #{[src,dest].flatten.join ' '}" if options[:verbose]
    return if options[:noop]
    fu_each_src_dest(src, dest) do |s, d|
      copy_file_in_bar bar, s, d, options[:preserve]
    end
  end
  module_function :cp_in_bar

  def cp_r_in_bar(bar, src, dest, options = {})
    fu_check_options options, OPT_TABLE['cp_r']
    fu_output_message "cp -r#{options[:preserve] ? 'p' : ''}#{options[:remove_destination] ? ' --remove-destination' : ''} #{[src,dest].flatten.join ' '}" if options[:verbose]
    return if options[:noop]
    options[:dereference_root] = true unless options.key?(:dereference_root)
    fu_each_src_dest(src, dest) do |s, d|
      copy_entry_in_bar bar, s, d, options[:preserve], options[:dereference_root], options[:remove_destination]
    end
  end
  module_function :cp_r_in_bar

  def copy_entry_in_bar(bar, src, dest, preserve = false, dereference_root = false, remove_destination = false)
    Entry_.new(src, nil, dereference_root).traverse do |ent|
      destent = Entry_.new(dest, ent.rel, false)
      File.unlink destent.path if remove_destination && File.file?(destent.path)
      ent.copy_in_bar bar, destent.path
      ent.copy_metadata destent.path if preserve
    end
  end
  module_function :copy_entry_in_bar

  def copy_file_in_bar(bar, src, dest, preserve = false, dereference = true)
    ent = Entry_.new(src, nil, dereference)
    ent.copy_file_in_bar bar, dest
    ent.copy_metadata dest if preserve
  end
  module_function :copy_file_in_bar

  def mv_in_bar(bar, src, dest, options = {})
    fu_check_options options, OPT_TABLE['mv']
    fu_output_message "mv#{options[:force] ? ' -f' : ''} #{[src,dest].flatten.join ' '}" if options[:verbose]
    return if options[:noop]
    fu_each_src_dest(src, dest) do |s, d|
      destent = Entry_.new(d, nil, true)
      begin
        if destent.exist?
          if destent.directory?
            raise Errno::EEXIST, dest
          else
            destent.remove_file if rename_cannot_overwrite_file?
          end
        end
        begin
          File.rename s, d
        rescue Errno::EXDEV
          copy_entry_in_bar bar, s, d, true
          if options[:secure]
            remove_entry_secure s, options[:force]
          else
            remove_entry s, options[:force]
          end
        end
      rescue SystemCallError
        raise unless options[:force]
      end
    end
  end
  module_function :mv_in_bar

  module StreamUtils_
    def fu_copy_stream0_in_bar(bar, src, dest, blksize)   #:nodoc:
			report = false
			if File.size?(src)
				report = true
				ticks = File.size(src) / blksize
				bar.max = ticks
				bar.counter = i = MutableNumber.new(0)
				log('.')
			end
			txt = "cp #{File.basename(src.path)} ..."
			bar.set_text_prefix(txt)

      while s = src.read(blksize)
        dest.write s
				i.add 1
      end
    end
  end

  class Entry_   #:nodoc: internal use only
    def copy_in_bar(bar, dest)
      case
      when file?
        copy_file_in_bar bar, dest
      when directory?
        begin
          Dir.mkdir dest
        rescue
          raise unless File.directory?(dest)
        end
      when symlink?
        File.symlink File.readlink(path()), dest
      when chardev?
        raise "cannot handle device file" unless File.respond_to?(:mknod)
        mknod dest, ?c, 0666, lstat().rdev
      when blockdev?
        raise "cannot handle device file" unless File.respond_to?(:mknod)
        mknod dest, ?b, 0666, lstat().rdev
      when socket?
        raise "cannot handle socket" unless File.respond_to?(:mknod)
        mknod dest, nil, lstat().mode, 0
      when pipe?
        raise "cannot handle FIFO" unless File.respond_to?(:mkfifo)
        mkfifo dest, 0666
      when door?
        raise "cannot handle door: #{path()}"
      else
        raise "unknown file type: #{path()}"
      end
    end

    def copy_file_in_bar(bar, dest)
      st = stat()
      File.open(path(),  'rb') {|r|
        File.open(dest, 'wb', st.mode) {|w|
          fu_copy_stream0_in_bar bar, r, w, (fu_blksize(st) || fu_default_blksize())
        }
      }
    end
  end
end
