def screensaver
	cleari

	str = Time.now.to_s
	s = Fm.cols - str.size
	s = 1 if s < 0

	puti((Fm.lines.to_f/2).floor, s/2, str)
#	puti(rand(Fm.lines), rand(Fm.cols), 'MEDITONSIN')
end
