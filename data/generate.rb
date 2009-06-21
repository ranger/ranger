#!/usr/bin/ruby
## Parses mime.types and creates mime.dat

file = File.read(ARGV[0] || "mime.types")

table = {}
for l in file.lines
	next if l[0] == ?#
	next unless l.size > 3
	next unless l.include? ?\t

	left, *exts = l.split(/\s+/)
#	print exts.inspect
	for ext in exts
		table[ext] = left
	end
end

File.open('mime.dat', 'w') do |f|
	f.write Marshal.dump(table)
end

