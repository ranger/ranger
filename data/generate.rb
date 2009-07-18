#!/usr/bin/ruby
## Parses mime.types and creates mime.dat

file = File.read(ARGV.first || "mime.types")

table = {}
for line in file.lines
	next if line[0] == ?# or
		line.size <= 3 or
		!line.include?( ?\t )

	name, *extensions = line.split(/\s+/)
	for ext in extensions
		table[ext] = name
	end
end

File.open( 'mime.dat', 'w' ) do |f|
	f.write Marshal.dump( table )
end

